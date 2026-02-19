<?php
// =============================================================================
// API endpoint: receives chat messages from the frontend and returns the
// agent's response (text + optional ui_action). Calls Python agent via shell.
// =============================================================================

// Disable displaying errors in the response (keep for production)
ini_set('display_errors', 0);
// Report all PHP errors internally (for logging)
error_reporting(E_ALL);

// CORS: allow requests from any origin (e.g. frontend on same or different port)
header("Access-Control-Allow-Origin: *");
// Response will be JSON with UTF-8 encoding
header("Content-Type: application/json; charset=UTF-8");
// Allow POST method
header("Access-Control-Allow-Methods: POST");
// Allow these headers in incoming requests
header("Access-Control-Allow-Headers: Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With");

// Optional helper to write debug lines to a log file (currently disabled)
function log_debug($msg)
{
    // file_put_contents("api_debug.log", "[" . date("Y-m-d H:i:s") . "] " . $msg . "\n", FILE_APPEND);
}

// Read the raw POST body (JSON string)
$raw_input = file_get_contents("php://input");
// Decode JSON into a PHP object
$data = json_decode($raw_input);

// Only process if both session_id and message are present
if (!empty($data->message) && !empty($data->session_id)) {
    // Sanitize: remove double quotes to avoid breaking the shell command
    $s_id = str_replace('"', '', $data->session_id);
    $msg = str_replace('"', '', $data->message);

    // Build command: set UTF-8 for Python output, then run agent_cli with session and message
    $command = "set PYTHONIOENCODING=utf-8 && python agent_cli.py --session_id \"$s_id\" --message \"$msg\"";

    // Execute the command and capture stdout (agent prints JSON to stdout)
    $output = shell_exec($command);

    // If the command returned nothing, return a 500 error
    if ($output === null || trim($output) === "") {
        http_response_code(500);
        echo json_encode(["error" => "Agent execution returned no output."]);
    }
    else {
        // Try to parse the output as JSON (agent prints json.dumps(response))
        $decoded = json_decode($output);
        if ($decoded) {
            // Valid JSON: send it through as-is to the frontend
            echo $output;
        }
        else {
            // Output was not valid JSON (e.g. Python traceback): wrap in a text response
            echo json_encode(["text" => trim($output)]);
        }
    }
}
else {
    // Missing required fields: return 400 Bad Request
    http_response_code(400);
    echo json_encode(["message" => "Incomplete data."]);
}
?>
