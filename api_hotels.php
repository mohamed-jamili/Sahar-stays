<?php
// =============================================================================
// API endpoint: returns the list of all hotels as JSON. Used by the frontend
// to display hotel cards. Calls get_hotels.py which reads from tools.HOTELS.
// =============================================================================

// CORS: allow requests from any origin
header("Access-Control-Allow-Origin: *");
// Response is JSON
header("Content-Type: application/json; charset=UTF-8");

// Run the Python script that prints the HOTELS list as JSON
$command = "set PYTHONIOENCODING=utf-8 && python get_hotels.py";
$output = shell_exec($command);

// If no output or empty, return 500 and an error message
if ($output === null || empty(trim($output))) {
    http_response_code(500);
    echo json_encode(["error" => "Failed to fetch hotels"]);
} else {
    // Output is already JSON; pass it through to the client
    echo $output;
}
?>
