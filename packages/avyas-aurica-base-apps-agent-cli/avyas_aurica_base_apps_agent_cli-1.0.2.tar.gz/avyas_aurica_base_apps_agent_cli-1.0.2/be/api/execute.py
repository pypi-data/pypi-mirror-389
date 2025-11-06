"""
Agent CLI API - Command execution interface for Digital Twin

Provides secure command execution capabilities on the execution node.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import subprocess
import asyncio
import os
import platform
import sys
from pathlib import Path
from datetime import datetime
import shlex
import uuid

router = APIRouter()

# Base paths
APPS_DIR = Path(__file__).parent.parent.parent.parent  # /apps directory
PROJECT_ROOT = APPS_DIR.parent  # /code directory

# Command execution state
_running_commands: Dict[str, Dict[str, Any]] = {}


class ExecuteCommandRequest(BaseModel):
    """Request to execute a command"""
    command: str
    cwd: Optional[str] = None
    timeout: Optional[int] = 30
    env: Optional[Dict[str, str]] = None


class CommandResponse(BaseModel):
    """Response from command execution"""
    command_id: str
    command: str
    returncode: int
    stdout: str
    stderr: str
    execution_time: float
    timestamp: str


def validate_working_directory(cwd: Optional[str]) -> Path:
    """
    Validate and resolve working directory.
    
    Args:
        cwd: Working directory path (absolute or relative to project root)
    
    Returns:
        Resolved absolute path
    
    Raises:
        HTTPException: If path is invalid or unsafe
    """
    if cwd is None:
        return PROJECT_ROOT
    
    try:
        # Handle both absolute and relative paths
        if Path(cwd).is_absolute():
            target_path = Path(cwd).resolve()
        else:
            target_path = (PROJECT_ROOT / cwd).resolve()
        
        # Security: Ensure path is within project root
        try:
            target_path.relative_to(PROJECT_ROOT)
        except ValueError:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied: Working directory must be within project root"
            )
        
        if not target_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Working directory not found: {cwd}"
            )
        
        if not target_path.is_dir():
            raise HTTPException(
                status_code=400,
                detail=f"Working directory is not a directory: {cwd}"
            )
        
        return target_path
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid working directory: {str(e)}")


def validate_command(command: str) -> bool:
    """
    Validate command for safety.
    
    Currently allows most commands but can be extended with restrictions.
    
    Args:
        command: Command to validate
    
    Returns:
        True if command is allowed
    
    Raises:
        HTTPException: If command is dangerous or not allowed
    """
    # List of dangerous patterns (can be extended)
    dangerous_patterns = [
        'rm -rf /',
        'dd if=',
        'mkfs',
        ':(){ :|:& };:',  # Fork bomb
    ]
    
    command_lower = command.lower().strip()
    
    for pattern in dangerous_patterns:
        if pattern in command_lower:
            raise HTTPException(
                status_code=403,
                detail=f"Command blocked: Contains dangerous pattern '{pattern}'"
            )
    
    return True


@router.post("/execute")
async def execute_command(request: ExecuteCommandRequest) -> CommandResponse:
    """
    Execute a command synchronously and return the result.
    
    Args:
        request: Command execution request
    
    Returns:
        Command execution result
    """
    # Validate command
    validate_command(request.command)
    
    # Validate working directory
    cwd = validate_working_directory(request.cwd)
    
    command_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    
    try:
        # Prepare environment
        env = os.environ.copy()
        if request.env:
            env.update(request.env)
        
        # Execute command
        process = await asyncio.create_subprocess_shell(
            request.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(cwd),
            env=env
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=request.timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise HTTPException(
                status_code=408,
                detail=f"Command execution timeout ({request.timeout}s)"
            )
        
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        return CommandResponse(
            command_id=command_id,
            command=request.command,
            returncode=process.returncode,
            stdout=stdout.decode('utf-8', errors='replace'),
            stderr=stderr.decode('utf-8', errors='replace'),
            execution_time=execution_time,
            timestamp=start_time.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Command execution error: {str(e)}"
        )


@router.post("/execute-async")
async def execute_command_async(request: ExecuteCommandRequest) -> Dict[str, Any]:
    """
    Execute a command asynchronously in the background.
    
    Args:
        request: Command execution request
    
    Returns:
        Command ID for tracking
    """
    # Validate command
    validate_command(request.command)
    
    # Validate working directory
    cwd = validate_working_directory(request.cwd)
    
    command_id = str(uuid.uuid4())
    
    # Store command info
    _running_commands[command_id] = {
        "command": request.command,
        "cwd": str(cwd),
        "status": "running",
        "start_time": datetime.utcnow().isoformat(),
        "process": None
    }
    
    # Start command in background
    async def run_background():
        try:
            env = os.environ.copy()
            if request.env:
                env.update(request.env)
            
            process = await asyncio.create_subprocess_shell(
                request.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd),
                env=env
            )
            
            _running_commands[command_id]["process"] = process
            
            stdout, stderr = await process.communicate()
            
            _running_commands[command_id].update({
                "status": "completed",
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace'),
                "end_time": datetime.utcnow().isoformat()
            })
        except Exception as e:
            _running_commands[command_id].update({
                "status": "error",
                "error": str(e),
                "end_time": datetime.utcnow().isoformat()
            })
    
    # Start task
    asyncio.create_task(run_background())
    
    return {
        "command_id": command_id,
        "command": request.command,
        "status": "started",
        "message": "Command started in background"
    }


@router.get("/status/{command_id}")
async def get_command_status(command_id: str) -> Dict[str, Any]:
    """
    Get the status of an async command.
    
    Args:
        command_id: Command ID from execute-async
    
    Returns:
        Command status
    """
    if command_id not in _running_commands:
        raise HTTPException(status_code=404, detail="Command not found")
    
    cmd_info = _running_commands[command_id].copy()
    # Remove process object from response
    cmd_info.pop('process', None)
    
    return cmd_info


@router.get("/output/{command_id}")
async def get_command_output(command_id: str) -> Dict[str, Any]:
    """
    Get the output of a completed command.
    
    Args:
        command_id: Command ID from execute-async
    
    Returns:
        Command output
    """
    if command_id not in _running_commands:
        raise HTTPException(status_code=404, detail="Command not found")
    
    cmd_info = _running_commands[command_id]
    
    if cmd_info["status"] == "running":
        raise HTTPException(status_code=425, detail="Command still running")
    
    return {
        "command_id": command_id,
        "command": cmd_info["command"],
        "status": cmd_info["status"],
        "returncode": cmd_info.get("returncode"),
        "stdout": cmd_info.get("stdout", ""),
        "stderr": cmd_info.get("stderr", ""),
        "error": cmd_info.get("error"),
        "start_time": cmd_info["start_time"],
        "end_time": cmd_info.get("end_time")
    }


@router.get("/system-info")
async def get_system_info() -> Dict[str, Any]:
    """
    Get system information about the execution node.
    
    Returns:
        System information
    """
    return {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": sys.version,
        "hostname": platform.node(),
        "cwd": str(Path.cwd()),
        "project_root": str(PROJECT_ROOT),
        "apps_directory": str(APPS_DIR),
        "user": os.getenv("USER") or os.getenv("USERNAME"),
        "shell": os.getenv("SHELL", "unknown")
    }


@router.get("/env")
async def get_environment_variables(
    filter: Optional[str] = Query(None, description="Filter environment variables by prefix")
) -> Dict[str, Any]:
    """
    Get environment variables (filtered for security).
    
    Args:
        filter: Optional prefix to filter variables
    
    Returns:
        Environment variables
    """
    # List of safe environment variables to expose
    safe_vars = [
        "PATH", "HOME", "USER", "USERNAME", "SHELL", "LANG",
        "PWD", "OLDPWD", "TERM", "EDITOR",
        "PYTHON_VERSION", "VIRTUAL_ENV"
    ]
    
    env_vars = {}
    
    for key, value in os.environ.items():
        # Include safe vars or those matching filter
        if key in safe_vars or (filter and key.startswith(filter)):
            env_vars[key] = value
    
    return {
        "environment_variables": env_vars,
        "count": len(env_vars),
        "filtered": filter is not None
    }


@router.get("/list-commands")
async def list_running_commands() -> Dict[str, Any]:
    """
    List all running and recent async commands.
    
    Returns:
        List of commands
    """
    commands = []
    
    for command_id, cmd_info in _running_commands.items():
        commands.append({
            "command_id": command_id,
            "command": cmd_info["command"],
            "status": cmd_info["status"],
            "start_time": cmd_info["start_time"],
            "end_time": cmd_info.get("end_time")
        })
    
    return {
        "commands": commands,
        "count": len(commands)
    }
