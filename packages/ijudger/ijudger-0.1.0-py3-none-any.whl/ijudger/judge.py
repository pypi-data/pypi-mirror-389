import os
import json
import subprocess
import tempfile
import time
import shutil

def compile_cpp(source_path, exe_path):
    try:
        result = subprocess.run(
            ["g++", "-O2", "-std=c++17", source_path, "-o", exe_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
        )
        if result.returncode != 0:
            return False, result.stderr
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "Compilation timed out"

def run_with_firejail(executable, input_data, time_limit, memory_limit=None, is_python=False):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as fin, \
         tempfile.NamedTemporaryFile(mode='w+', delete=False) as fout, \
         tempfile.NamedTemporaryFile(mode='w+', delete=False) as ferr:

        fin.write(input_data)
        fin.flush()

        if is_python:
            run_cmd = f"ulimit -v {memory_limit*1024 if memory_limit else 'unlimited'}; exec python3 -u {executable}"
        else:
            run_cmd = f"ulimit -v {memory_limit*1024 if memory_limit else 'unlimited'}; exec {executable}"

        cmd = ["firejail", "--quiet", "bash", "-c", run_cmd]

        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                stdin=open(fin.name, 'r'),
                stdout=open(fout.name, 'w'),
                stderr=open(ferr.name, 'w'),
                timeout=time_limit
            )
            end_time = time.time()
        except subprocess.TimeoutExpired:
            os.unlink(fin.name)
            os.unlink(fout.name)
            os.unlink(ferr.name)
            return "TLE", time_limit, None, ""
        except Exception:
            os.unlink(fin.name)
            os.unlink(fout.name)
            os.unlink(ferr.name)
            return "RE", 0, None, ""

        with open(fout.name, 'r') as f:
            user_output = f.read()
        with open(ferr.name, 'r') as f:
            err_output = f.read()

        returncode = result.returncode

        os.unlink(fin.name)
        os.unlink(fout.name)
        os.unlink(ferr.name)

        return user_output, end_time-start_time, returncode, err_output

def judge(problem_json_path, source_code_path, language):
    with open(problem_json_path, 'r') as f:
        problem = json.load(f)

    time_limit = problem["time_limit"]
    memory_limit = problem.get("memory_limit", None)
    test_cases = problem["test_cases"]

    tmp_dir = tempfile.mkdtemp()
    results = []

    exe_path = os.path.join(tmp_dir, "prog")
    if language == "cpp":
        ok, err = compile_cpp(source_code_path, exe_path)
        if not ok:
            shutil.rmtree(tmp_dir)
            return [{"status":"CE", "time":0, "error":err}]
        is_python = False
    elif language == "py":
        exe_path = source_code_path
        is_python = True
    else:
        shutil.rmtree(tmp_dir)
        raise ValueError("Unsupported language")

    for case in test_cases:
        input_data = case["input"]
        expected_output = case["output"]

        output, t, returncode, err = run_with_firejail(exe_path, input_data, time_limit, memory_limit, is_python)
        if output == "TLE":
            status = "TLE"
        elif returncode != 0:
            status = "RE/MLE"
        else:
            status = "AC" if output.strip() == expected_output.strip() else "WA"


        results.append({
            "status": status,
            "time": round(t, 3),
            "error": err
        })

    shutil.rmtree(tmp_dir)
    return results

if __name__ == "__main__":
    problem_json = "aplusb.json"
    source_code = "aplusb.cpp"
    lang = "cpp"
    res = judge(problem_json, source_code, lang)
    for i, r in enumerate(res):
        print(f"C++ Test case {i}: {r}")
    source_code = "aplusb.py"
    lang = "py"
    res = judge(problem_json, source_code, lang)
    for i, r in enumerate(res):
        print(f"Python Test case {i}: {r}")
