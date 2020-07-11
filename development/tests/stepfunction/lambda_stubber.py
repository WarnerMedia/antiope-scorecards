from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading

lock = threading.Lock()
DEFAULT_RESPONSE = {}

def read_chunked_transfer(rfile):
    data_so_far = bytearray()
    data = bytearray()
    while byte := rfile.read(1):
        if byte == b'\r':
            # print('found end of chunk')
            rfile.read(1) # just eat the \n
            # print(data_so_far)
            chunk_length = int(data_so_far.decode('utf-8'), 16)
            # print(chunk_length)
            if chunk_length == 0:
                # print('chunk size 0')
                break
            # print('getting chunk data', chunk_length)
            data.extend(rfile.read(chunk_length))
            # print(incoming_event)
            rfile.read(2) # just eat the \r\n after the chunk
            data_so_far = bytearray()
        else:
            data_so_far.extend(byte)
    return data

class LambdaStubServer(BaseHTTPRequestHandler):
    expected_calls = {}
    calls = []
    def do_POST(self): # pylint: disable=invalid-name,too-many-statements
        with lock:
            # parse path to get function name
            split_path = self.path.split('/')
            function_name = split_path[3]
            # print(self.headers)
            length = int(self.headers.get('content-length', '-1'))
            if length > 0:
                incoming_event = self.rfile.read(length)
            else: # chunked transfer
                incoming_event = read_chunked_transfer(self.rfile)
            try:
                parsed_event = json.loads(incoming_event)
            except json.decoder.JSONDecodeError:
                parsed_event = None
            call_record = {
                'functionName': function_name,
                'received': parsed_event,
            }
            is_error = False
            if function_name not in self.expected_calls:
                call_record.update({
                    'expected': None,
                    'error': 'Function name not present in expected calls',
                })
                response = DEFAULT_RESPONSE
            else:
                # critical section
                # find expected call
                # get first call (or list of parallel calls) from expected call list for function
                try:
                    expected_call = self.expected_calls[function_name][0]
                except IndexError:
                    expected_call = None

                if isinstance(expected_call, list): # check if call is one of several in parallel list
                    found_call = None
                    # look for expected calls in list of parallel calls
                    for idx, call in enumerate(expected_call):
                        if call['expected'] == parsed_event:
                            # found a matching call
                            found_call = expected_call.pop(idx)
                            # remove empty list of parallel calls from outer call list
                            if len(expected_call) == 0:
                                self.expected_calls[function_name].pop()
                            break
                    expected_call = found_call
                elif expected_call:
                    # remove call from list
                    self.expected_calls[function_name].pop(0)

                if expected_call:
                    call_record['expected'] = expected_call['expected']
                    if parsed_event != expected_call['expected']:
                        call_record['error'] = 'Received does not match expected'
                    response = expected_call['reply']
                    is_error = expected_call.get('error', False)
                else:
                    call_record['expected'] = None
                    call_record['error'] = 'Call not expected'
                    response = DEFAULT_RESPONSE

            self.calls.append(call_record)
            self.send_response(200)
            if 'content-type' in response:
                content_type = response['content-type']
                bytes_response = bytes(response['body'], 'utf-8')
            else:
                content_type = 'application/json'
                bytes_response = bytes(json.dumps(response), 'utf-8')
            self.send_header('connection', 'close')
            self.send_header('content-type', content_type)
            self.send_header('content-length', str(len(bytes_response)))
            if is_error:
                self.send_header('x-amz-function-error', 'Unhandled')
            self.end_headers()
            self.wfile.write(bytes_response)


def start_lambda_stubs(host, port, expected_calls):
    LambdaStubServer.expected_calls = expected_calls
    LambdaStubServer.calls = []
    def start_server():
        try:
            server = ThreadingHTTPServer((host, port), LambdaStubServer)
            server.serve_forever()
        except OSError: # catch if server is already started
            pass

    thread = threading.Thread(name='HTTPServer', target=start_server, daemon=True)
    thread.start()
    return thread

def get_results():
    return LambdaStubServer.calls
