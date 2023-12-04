### Setup
#### Get the script
```
git clone -b autorun https://github.com/yangkunx/applications.benchmarking.benchmark.platform-hero-features.git
```

#### Install deps 
```
pip install gitpython
```

#### Update the Weekly llm version
- Create new branch form latest develop branch
```
> git checkout develop
> git checkout -b ww39
```
- Modifiy the version of dev and oob llm in stack
  - modify the Dockerfile.2.intel_dev_llm in the path of stack/PyTorch-Xeon/
  - modify the Dockerfile.2.oob_llm in the path of stack/PyTorch-Xeon/
- Push the new branch (such as ww39)
#### Modify the script
- Modify run_case.py, change the value of `base_path`  in run_case.py which is store the path of the script repo. for example: /home/root/fork, the `/home/yangkun/lab/yangkunx` is store the path of the script repo.
```
ls -l /home/yangkun/lab/yangkunx
total 8
drwxrwxr-x  2 yangkun yangkun 4096 Aug  7 05:49 autorun
```
- Modify run_case.py, change the value of `repo_dir_name` and  `branch_name` in run_case.py which is the name of new branch (such as ww39).
### Run the script
- **--h**: Specify the hosts of execute script，the default value is `172.17.29.24`.
- **--n**: Specify the tag of push to dashbord，the default value is `ww22.1`.
- **--b**: Specify the backend of run wl pkm，the default value is `terraform`.
- **--p**: Specify the platform of run wl pkm，the default value is `SPR`.
- **--d**:  Specify whether to use dry-run，the default value is `False`.

#### Run on SPR
```
cd autorun

Python3 run_case_class.py --h "172.17.29.24" --n "ww32.1"
```

#### Run on EMR
```
cd autorun

Python3 run_case.py --h "172.17.29.24" --n "ww32.1" --p "EMR"
```