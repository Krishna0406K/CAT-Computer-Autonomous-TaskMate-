import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global router instance for caching
_laya_router = None

def get_router():
    global _laya_router
    if _laya_router is None:
        try:
            from laya import Router
            logger.info("Initializing LAYA Router...")
            # The Router() automatically handles loading the correct ONNX/HF weights
            _laya_router = Router() 
        except ImportError:
            logger.error("Failed to import LAYA. Please run 'pip install laya'.")
            raise
    return _laya_router

def evaluate_command_risk(command: str) -> str:
    """
    Uses the official LAYA SDK to dynamically score terminal command risk.
    Returns: "LOW", "MEDIUM", "HIGH", or "CRITICAL"
    """
    try:
        router = get_router()
        
        # State: The data LAYA is analyzing
        state = {
            "command": command,
            "context": "An AI agent wants to execute this command on the user's local operating system."
        }
        
        # Questions: The structured decision we need LAYA to make
        questions = {
            "security_risk": {
                "type": "choice",
                "instructions": "Classify the security risk of this command.",
                "criteria": {
                    "LOW": "Safe, purely informational read-only commands (e.g., echo, ls, pwd, cat)",
                    "MEDIUM": "Minor state changes or safe network calls (e.g., ping, curl, mkdir)",
                    "HIGH": "Modifies files or system configuration (e.g., rm, mv, npm install, pip install)",
                    "CRITICAL": "Destructive, dangerous, or unauthorized access (e.g., rm -rf /, format, granting root permissions)"
                }
            }
        }
        
        # Run the non-autoregressive forward pass
        result = router.predict(state, questions)
        
        # Extract the choice
        risk = result["answers"]["security_risk"]["choice"].upper()
        
        # Ensure the output matches our exact enum, otherwise fallback
        if risk in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            return risk
        return "CRITICAL"
        
    except Exception as e:
        logger.error(f"LAYA Evaluation failed, defaulting to CRITICAL. Error: {str(e)}")
        return "CRITICAL"
