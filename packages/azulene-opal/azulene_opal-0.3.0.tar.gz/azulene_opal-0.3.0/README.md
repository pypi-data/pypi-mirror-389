# opal-cli

## How to download OPAL CLI

```shellscript
pip install azulene-opal
```

## CLI Commands (macOS, Linux, Windows)

```shellscript
# Auth
python -m opal.main login --email user@example.com --password pass123
python -m opal.main whoami
python -m opal.main logout

# Jobs
python -m opal.main jobs submit --job-type xtb_calculation --input-data '{"numbers":[1,1], "positions":[[0,0,0],[0.74,0,0]]}'
python -m opal.main jobs cancel --job-id abc123
python -m opal.main jobs get --job-id abc123
python -m opal.main jobs get-jobs
python -m opal.main jobs check-running-jobs
python -m opal.main jobs get-job-types
python -m opal.main jobs check-health
```


### **Help Commands**

```bash
python -m opal.main --help

python -m opal.main jobs --help

python -m opal.main jobs submit --help
```

### **Auth Commands**

```bash
# Log in
python -m opal.main login --email your@email.com --password yourpassword

# Who am I (get current user info)
python -m opal.main whoami

# Log out
python -m opal.main logout
```

---

### **Job Commands**

```bash
# Submit a job (CMD)
python -m opal.main jobs submit --job-type generate_conformers --input-data "{\"smiles\": \"CCO\", \"num_conformers\": 5}"

# Submit a job (Git Bash / WSL / Linux / macOS)
python -m opal.main jobs submit --job-type generate_conformers --input-data '{"smiles": "CCO", "num_conformers": 5}'

# Submit a job (Powershell)
python -m opal.main jobs submit --job-type generate_conformers --input-data '{\"smiles\": \"CCO\", \"num_conformers\": 5}'

# List all jobs
python -m opal.main jobs get-jobs

# Get a specific job by ID
python -m opal.main jobs get --job-id YOUR_JOB_ID

# Cancel a job by ID
python -m opal.main jobs cancel --job-id YOUR_JOB_ID

# Poll modal for job status/results
python -m opal.main jobs check-running-jobs

# Health check
python -m opal.main jobs check-health

# Get available job types 
python -m opal.main jobs get-job-types
```

---


## Examples of Using the Library in Python

```shellscript
from opal import auth, jobs

# 1. Log in
auth.login(email="test@example.com", password="pass123")

# 2. Who am I
print(auth.whoami())

# 3. Submit a job
jobs.submit(job_type="generate_conformers",input_data={"smiles": "CCO", "num_conformers": 5}) # dict
# jobs.submit(job_type="generate_conformers",input_data='{"smiles": "CCO", "num_conformers": 5}') # str

# 4. List all jobs
print(jobs.get_jobs())

# 5. Get a specific job
print(jobs.get(job_id="YOUR_JOB_ID"))

# 6. Cancel a job
print(jobs.cancel(job_id="YOUR_JOB_ID"))

# 7. Poll job statuses
jobs.poll()

# 8. Health check
print(jobs.check_health())

# 9. Get job types
print(jobs.get_job_types())

# 10. Log out
auth.logout()
```


### Tips

* Wrap JSON input in single quotes (`'{"key": "value"}'`) and escape double quotes on Windows if needed.
* Replace `YOUR_JOB_ID` with actual returned IDs from `list-all` or `submit`.

---



**All Rights Reserved**
