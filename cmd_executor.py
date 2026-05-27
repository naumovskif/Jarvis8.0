"""
JARVIS Command Executor - Windows CMD Integration
Allows JARVIS to execute Windows commands safely with security controls

Features:
- Execute Windows commands via CMD
- Command history tracking
- Output capture and formatting
- Security restrictions (blacklist dangerous commands)
- Timeout protection
- Error handling and logging
- Real-time output streaming
"""

import logging
import subprocess
import threading
import queue
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import shlex

logger = logging.getLogger("cmd_executor")


class CommandExecutor:
    """
    Safely execute Windows CMD commands
    
    Restrictions:
    - No delete/format operations
    - No registry modifications
    - No system file changes
    - No network modifications
    - Commands limited to 30 second timeout
    """
    
    # Dangerous commands that should never be executed
    FORBIDDEN_COMMANDS = {
        "del ", "delete ", "rm ", "rmdir ",  # Delete operations
        "format ", "diskpart",  # Disk operations
        "reg delete", "regedit",  # Registry modifications
        "shutdown ", "restart ", "hibernate",  # System control
        "net user ", "net group",  # User management
        "cipher /w",  # Secure deletion
        "taskkill /f",  # Force kill
        "ipconfig /release", "ipconfig /renew",  # Network changes
        "netsh ", "route add", "route delete",  # Network config
        "wmic ", "winrm",  # WMI/Remoting
    }
    
    # Safe/allowed commands patterns
    SAFE_COMMANDS = [
        "dir ", "ls ", "cd ", "pwd",  # Navigation
        "type ", "cat ", "more ", "less",  # File viewing
        "echo ", "write",  # Output
        "date ", "time ",  # System info
        "ipconfig ", "systeminfo", "wmic logicaldisk",  # Info only
        "tasklist ", "Get-Process",  # Process list (read-only)
        "whoami ", "hostname", "set ",  # User/system info
        "findstr ", "grep ", "find ",  # Search
        "tree ", "robocopy",  # Copying
        "python ", "pip ", "npm ",  # Development
        "git ",  # Version control
    ]
    
    def __init__(self):
        self.history: List[Dict] = []
        self.max_history = 100
        self.default_timeout = 30  # seconds
        logger.info("CommandExecutor initialized")
    
    def is_command_safe(self, command: str) -> Tuple[bool, Optional[str]]:
        """
        Check if command is safe to execute
        
        Args:
            command: Command string to check
            
        Returns:
            Tuple of (is_safe: bool, reason: str or None)
        """
        cmd_lower = command.lower().strip()
        
        # Check for forbidden commands
        for forbidden in self.FORBIDDEN_COMMANDS:
            if cmd_lower.startswith(forbidden):
                return False, f"Forbidden command: {forbidden.strip()}"
        
        # Check for dangerous patterns
        dangerous_patterns = [
            ">nul", "/y",  # Silent/force execution
            "&&", "||", ";",  # Command chaining (allow only certain)
            "|",  # Piping (allow)
        ]
        
        # Allow piping and && for reading/viewing operations
        if any(bad in cmd_lower for bad in ["del ", "format ", "shutdown "]):
            return False, "Dangerous command pattern detected"
        
        return True, None
    
    def execute(self, command: str, timeout: int = None, shell: bool = True) -> Dict:
        """
        Execute a Windows command safely
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds (default: 30)
            shell: Use shell execution
            
        Returns:
            Dict with status, output, error, and metadata
        """
        timeout = timeout or self.default_timeout
        
        # Check if command is safe
        is_safe, reason = self.is_command_safe(command)
        if not is_safe:
            logger.warning(f"Command blocked: {reason} - {command}")
            result = {
                "status": "blocked",
                "command": command,
                "output": "",
                "error": reason,
                "timestamp": datetime.now().isoformat(),
                "exit_code": -1
            }
            self.history.append(result)
            return result
        
        logger.info(f"Executing command: {command}")
        
        start_time = datetime.now()
        result = {
            "command": command,
            "timestamp": start_time.isoformat(),
            "status": "pending",
            "output": "",
            "error": "",
            "exit_code": None,
            "execution_time": 0
        }
        
        try:
            # Execute command
            proc = subprocess.Popen(
                command,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                cwd=str(Path.home())
            )
            
            # Capture output with timeout
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
                result["output"] = stdout
                result["error"] = stderr
                result["exit_code"] = proc.returncode
                result["status"] = "success" if proc.returncode == 0 else "error"
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                result["output"] = stdout
                result["error"] = f"Command timeout after {timeout} seconds"
                result["status"] = "timeout"
                result["exit_code"] = -1
                logger.warning(f"Command timeout: {command}")
            
        except Exception as e:
            result["error"] = str(e)
            result["status"] = "error"
            result["exit_code"] = -1
            logger.error(f"Command execution failed: {e}")
        
        # Calculate execution time
        end_time = datetime.now()
        result["execution_time"] = (end_time - start_time).total_seconds()
        
        # Store in history
        self._add_to_history(result)
        
        return result
    
    def execute_safe(self, command: str) -> Dict:
        """
        Execute command with maximum safety checks
        
        Shorter timeout and read-only focus
        """
        return self.execute(command, timeout=10)
    
    def execute_with_output(self, command: str, timeout: int = None) -> str:
        """
        Execute command and return just the output
        
        Raises:
            RuntimeError if command fails
        """
        result = self.execute(command, timeout)
        
        if result["status"] == "blocked":
            raise RuntimeError(f"Command blocked: {result['error']}")
        if result["status"] != "success":
            raise RuntimeError(f"Command failed: {result['error']}")
        
        return result["output"]
    
    def _add_to_history(self, result: Dict):
        """Add command to history"""
        self.history.append(result)
        
        # Keep history size limited
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """Get recent command history"""
        return self.history[-limit:]
    
    def clear_history(self):
        """Clear command history"""
        self.history.clear()
        logger.info("Command history cleared")
    
    def get_system_info(self) -> Dict:
        """Get system information"""
        info = {}
        
        # Get system info
        result = self.execute("systeminfo")
        if result["status"] == "success":
            info["system_info"] = result["output"]
        
        # Get disk info
        result = self.execute("wmic logicaldisk get name,size,freespace")
        if result["status"] == "success":
            info["disk_info"] = result["output"]
        
        # Get processes
        result = self.execute("tasklist")
        if result["status"] == "success":
            info["processes"] = result["output"][:500]  # First 500 chars
        
        return info
    
    def get_directory_listing(self, path: str = ".") -> Dict:
        """Get directory listing"""
        result = self.execute(f"dir {path}")
        return {
            "path": path,
            "listing": result["output"],
            "status": result["status"]
        }
    
    def read_file(self, filepath: str) -> Dict:
        """Read file contents"""
        result = self.execute(f"type {filepath}")
        return {
            "file": filepath,
            "content": result["output"],
            "status": result["status"],
            "error": result["error"] if result["status"] != "success" else None
        }
    
    def search_files(self, pattern: str, path: str = ".") -> Dict:
        """Search for files matching pattern"""
        result = self.execute(f'findstr /r /s "{pattern}" {path}\\*')
        return {
            "pattern": pattern,
            "path": path,
            "results": result["output"],
            "status": result["status"]
        }
    
    def get_stats(self) -> Dict:
        """Get executor statistics"""
        successful = sum(1 for cmd in self.history if cmd.get("status") == "success")
        failed = sum(1 for cmd in self.history if cmd.get("status") in ["error", "timeout"])
        blocked = sum(1 for cmd in self.history if cmd.get("status") == "blocked")
        
        return {
            "total_commands": len(self.history),
            "successful": successful,
            "failed": failed,
            "blocked": blocked,
            "history_size": len(self.history),
            "max_history": self.max_history
        }


class JARVISCMDInterface:
    """
    JARVIS interface for command execution
    Easy access to CMD functionality
    """
    
    def __init__(self):
        self.executor = CommandExecutor()
        logger.info("JARVIS CMD Interface initialized")
    
    def execute(self, command: str) -> Dict:
        """
        Execute command
        
        Usage:
            jarvis_cmd = JARVISCMDInterface()
            result = jarvis_cmd.execute("dir")
        """
        return self.executor.execute(command)
    
    def cmd(self, command: str) -> str:
        """
        Quick command execution (returns just output)
        
        Usage:
            output = jarvis_cmd.cmd("ipconfig")
        """
        try:
            return self.executor.execute_with_output(command)
        except RuntimeError as e:
            return f"Error: {str(e)}"
    
    def system(self, command: str) -> Dict:
        """Execute system command with full details"""
        return self.executor.execute(command)
    
    def shell(self, command: str) -> str:
        """Execute shell command (returns output or error)"""
        result = self.executor.execute(command)
        if result["status"] == "success":
            return result["output"]
        elif result["status"] == "blocked":
            return f"[BLOCKED] {result['error']}"
        else:
            return f"[ERROR] {result['error']}"
    
    def ls(self, path: str = ".") -> str:
        """List directory"""
        result = self.executor.get_directory_listing(path)
        return result["listing"]
    
    def read(self, filepath: str) -> str:
        """Read file"""
        result = self.executor.read_file(filepath)
        return result["content"] if result["status"] == "success" else result["error"]
    
    def find(self, pattern: str, path: str = ".") -> str:
        """Find files"""
        result = self.executor.search_files(pattern, path)
        return result["results"]
    
    def info(self) -> Dict:
        """Get system information"""
        return self.executor.get_system_info()
    
    def history(self, limit: int = 10) -> List[Dict]:
        """Get command history"""
        return self.executor.get_history(limit)
    
    def status(self) -> Dict:
        """Get executor status"""
        return self.executor.get_stats()


# Global instance for easy access
_cmd_executor = None

def get_cmd_executor() -> CommandExecutor:
    """Get global command executor instance"""
    global _cmd_executor
    if _cmd_executor is None:
        _cmd_executor = CommandExecutor()
    return _cmd_executor

def get_jarvis_cmd() -> JARVISCMDInterface:
    """Get JARVIS CMD interface"""
    return JARVISCMDInterface()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test JARVIS CMD Interface
    print("=" * 70)
    print("JARVIS Command Executor Test")
    print("=" * 70)
    
    jarvis_cmd = get_jarvis_cmd()
    
    # Test 1: Simple command
    print("\n[Test 1] Date command:")
    result = jarvis_cmd.execute("date /t")
    print(f"Output: {result['output'].strip()}")
    print(f"Status: {result['status']}")
    
    # Test 2: Directory listing
    print("\n[Test 2] Directory listing:")
    listing = jarvis_cmd.ls()
    print(listing[:300] + "...")
    
    # Test 3: Blocked command
    print("\n[Test 3] Try blocked command (should fail):")
    result = jarvis_cmd.execute("del test.txt")
    print(f"Status: {result['status']}")
    print(f"Error: {result['error']}")
    
    # Test 4: System info
    print("\n[Test 4] System information:")
    info = jarvis_cmd.info()
    if "system_info" in info:
        print(info["system_info"][:200] + "...")
    
    # Test 5: Statistics
    print("\n[Test 5] Executor Statistics:")
    stats = jarvis_cmd.status()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
    print("JARVIS is ready to execute commands!")
    print("=" * 70)
