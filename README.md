# DiagAnalyzer
Diaganalyzer is a user bahavior analysis tool for Eventtranscript.db. This is just a prototype of the Diaganalyzer. It will be updated for stability, dependency, and so on.


# Basic Usage
Diaganalyzer needs to two options which are input file path and analysis option. Examples of usages are following : 

```
>> python diaganalyzer.py --help
>> python diaganalyzer.py -i .\EventTranscript.db -o usb
>> python diaganalyzer.py -i .\EventTranscript.db -o browser 
>> python diaganalyzer.py -i .\EventTranscript.db -o wifi
```
Then, you can see analysis reports in ```[installed dir]\report\``` directory. There are sample reports in [```\report_samples\```](https://github.com/L4wk3R/DiagAnalyzer/tree/main/report_samples) in this repository.
