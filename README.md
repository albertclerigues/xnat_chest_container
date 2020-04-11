# xnat_chest_container
Xnat container specification for chest xray image processing

### Debugging the container

The standard and error output of a container execution in XNAT can be accessed by:

1. Finding the log's path of the last container execution by showing the last 30 lines of the log by running:

  `tail -n 30 /data/xnat/home/logs/containers.log` 


2. Find the line that says something like:

  `2020-04-11 09:15:52,790 [multThreadedQueueDispatcher-5] INFO  org.nrg.containers.services.impl.ContainerFinalizeServiceImpl - Container 77: Saving logs to /data/xnat/archive/CONTAINER_EXEC/20200411_091552/LOGS/`


3. Access the standard and error logs located in:

    `/data/xnat/archive/CONTAINER_EXEC/20200411_091552/LOGS/stderr.log`

    `/data/xnat/archive/CONTAINER_EXEC/20200411_091552/LOGS/stdout.log`
