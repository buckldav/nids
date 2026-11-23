## Setup and Run 

### 

### Run the server

Read the file, what does it do?

```bash
sh run.sh
```

## Assignment

### 1. 

How could you `ls` the directory in `_res_dir()`.

```python
def _res_file(self, full_path: str):
    self.send_response(200)
    self.end_headers()
    # cat the file and write to the response stream
    res = subprocess.run(["sudo", "cat", full_path], capture_output=True, text=True)
    self.wfile.write(res.stdout.encode())

def _res_dir(self, full_path: str):
    self.send_response(200)
    self.end_headers()
    # TODO: ls the directory write to the response stream
```