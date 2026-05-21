from utils.logger import setup_logger

logger = setup_logger("inquiry_service")

def get_expected_cable_count(serial_number: str) -> int:
    """
    Dummy service that simulates a backend inquiry to telecom database
    Returns the expected number of cables installed for the given ODP serial.
    """
    logger.info(f"Querying backend for ODP serial: {serial_number}...")
    
    # We return a fixed number for the demo so the user can reliably test the UI.
    # In a real scenario, this would make an HTTP request to LinkNet API.
    expected_cables = 4
    
    logger.info(f"Inquiry Service Response: ODP {serial_number} should have {expected_cables} cables")
    return expected_cables
