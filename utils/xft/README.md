### Use xft.py
#### Install deps 
```
pip install pandas paramiko tabulate
```
#### Parameters
- **--ww**: Specify the weekly,the default value is `40`.
- **--weekly | --w**: Specify run the weekly case, the default value is `False`.
- **--bi-weekly | --bw**: Specify run the bi-weekly case, the default value is `False`.
- **--weekly | --w**: Specify run the monthly case, the default value is `False`.
- **--normal | --n**:  Specify run the other nomal case, the default value is `False`.
- **--test | --t**:  Specify run test case , the default value is `False`.
- **--dry_run | --d**:  dry run case , the default value is `False`.
- **--only_parse | --o**:  Specify only parse the log and not run case , the default value is `False`.
- **--root_dir | --rd**: Specify the path of wsf code and exec script root_dir ,the default value is `.`.
- **--platform | --p**: Specify the platform of run case ,the default value is `spr`.
- **--repo | --r**: Specify the repo of wsf ,the default value is `https://github.com/yangkunx/applications.benchmarking.benchmark.platform-hero-features`.
- **--branch | --b**: Specify the branch of wsf repo ,the default value is `develop`.
- **--log_file | --l**: Specify the name of log file ,the default value is `output.log`.

#### Run script
**Weekly**: only print the run cmd

```
python3 xft.py  --ww 51  --weekly --d
or
python3 xft.py  --ww 51  --w --d
```
**Weekly**: run run weekly test cmd and output to the output.log
```
python3 xft.py  --ww 51 --weekly 2>&1 | tee output.log
or
python3 xft.py  --ww 51 --w 2>&1 | tee output.log
```

**Bi-weekly**: only print the run cmd
```
python3 xft.py  --ww 51  --bi-weekly --d
or
python3 xft.py  --ww 51  --bw --d
```
**Bi-weekly**: run run bi-weekly test cmd and output to the output.log
```
python3 xft.py  --ww 51 --bi-weekly 2>&1 | tee output.log
or
python3 xft.py  --ww 51 --bw 2>&1 | tee output.log
```

**Monthly**: only print the run cmd
```
python3 xft.py  --ww 51  --monthly --d
or
python3 xft.py  --ww 51  --m --d
```
**Monthly**: run run monthly test cmd and output to the output.log
```
python3 xft.py  --ww 51 --monthly 2>&1 | tee output.log
or
python3 xft.py  --ww 51 --m 2>&1 | tee output.log
```

Run the test case
```
python3 xft.py  --ww 51 --w --t
```

Only parse the ouput*.log:
```
python3 xft.py --o
```
Only parse the ouput.log:
```
python3 xft.py --o --l output.log
```
    
