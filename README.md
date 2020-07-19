# XNAT COVID19 container
XNAT container for COVID19 inference.


## Docker build:

Build the docker with the pertinent version `ver` as:

```bash

docker build -f Dockerfile -t sergivalverde/covid19_xray_prediction:ver

```

## Version

- 0.4: Resnet 512 + ROI (19 July 2020)


## Debugging

The standard and error output of a container execution in XNAT can be accessed by:

1. Finding the log's path of the last container execution by showing the last 30 lines of the log by running:

  `tail -n 30 /data/xnat/home/logs/containers.log`


2. Find the line that says something like:

  `2020-04-11 09:15:52,790 [multThreadedQueueDispatcher-5] INFO  org.nrg.containers.services.impl.ContainerFinalizeServiceImpl - Container 77: Saving logs to /data/xnat/archive/CONTAINER_EXEC/20200411_091552/LOGS/`


3. Access the standard and error logs located in:

    `/data/xnat/archive/CONTAINER_EXEC/20200411_091552/LOGS/stderr.log`

    `/data/xnat/archive/CONTAINER_EXEC/20200411_091552/LOGS/stdout.log`
