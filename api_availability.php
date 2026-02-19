<?php
// =============================================================================
// API endpoint: returns booked date ranges for a hotel (for the calendar view).
// Expects GET parameter hotel_id. Calls get_availability.py (if it exists).
// =============================================================================

// CORS and JSON response headers
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");

// Get hotel_id from query string (e.g. ?hotel_id=h1)
$hotel_id = isset($_GET['hotel_id']) ? $_GET['hotel_id'] : '';

// Reject request if hotel_id is missing
if (empty($hotel_id)) {
    http_response_code(400);
    echo json_encode(["error" => "Missing hotel_id parameter."]);
    exit;
}

// Sanitize: only allow alphanumeric, underscore, hyphen (prevents shell injection)
if (!preg_match('/^[a-zA-Z0-9_\-]+$/', $hotel_id)) {
    http_response_code(400);
    echo json_encode(["error" => "Invalid hotel_id format."]);
    exit;
}

// Run Python script to get availability; script should print JSON array of {check_in, check_out}
$command = "set PYTHONIOENCODING=utf-8 && python get_availability.py --hotel_id \"$hotel_id\"";
$output = shell_exec($command);

// If no output, return 500
if ($output === null || empty(trim($output))) {
    http_response_code(500);
    echo json_encode(["error" => "Failed to fetch availability."]);
} else {
    // Pass through the JSON output (e.g. [] or list of date ranges)
    echo $output;
}
?>
