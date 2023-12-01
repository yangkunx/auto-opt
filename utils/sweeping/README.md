### Introduction
- **run_case.sh**: the shell script design to run LLM case that sweeping cpu core, batch_size and frequency.
- **parse_pandas.py**: the python script design to use pandas to collect and summary the result of run run_case.sh log, and saved to excel.
- **parse_to_excel.py**: the python script design to use openpyxl module to collect and summary the result of run run_case.sh log, and saved to excel.

### Script Execution

#### Execution the run_case.sh
#### Parameters
- **-h**: the Hardware platform of run case, default is "spr".
- **-l**: Run the case sequentially, default is "1".
- **-p**: run precison, default is "bfloat16".
- **-b**: run batch_size, default is "1".
- **-c**: run core, default is "56".
- **-f**: run frequencys, default is "3.8".
- **-s**: pass the args to ctest.sh, eg: [-s "INPUT_TOKENS=1024/OUTPUT_TOKENS=128"].
- **-d **:Generate he testcase configurations and then exit, default is "false", eg: [-d].  

For example:
Sweeping single core
```
sh run_case.sh -c "56"
``` 
Sweeping multiple cores
```
sh run_case.sh -c "50 51 52 54 56"
```
Sweeping single precison
```
sh run_case.sh -p "bfloat16"
```  
Sweeping multiple precisons
```
sh run_case.sh -c "bfloat16 woq_int8 static_int8"
``` 
Sweeping single batch_size
```
sh run_case.sh -b "16"
```
Sweeping multiple batch_sizes
```
sh run_case.sh -b "1 2 4 6 8 16"
```
Sweeping single frequency
```
sh run_case.sh -f "3.8"
```
Sweeping multiple frequencys
```
sh run_case.sh -f "2.0 2.4 2.8 3.8"
```
Test the run case configurations
```
sh run_case.sh -d
```

#### Execution the parse_pandas.py
#### Parameters
- **precision**: Specify the model precision, the supported precisions are `bfloat16` (default) or `woq_int8` (Weight only quantzation INT8) or `woq_int4` (Weight only quantzation INT4) or `static_int8` (Static quantzation INT8).
- **platform**: Specify the hardware platform is `SPR` or `EMR`.

For example:

```
sh run_case.sh --h "SPR" --p "bfloat16"
```