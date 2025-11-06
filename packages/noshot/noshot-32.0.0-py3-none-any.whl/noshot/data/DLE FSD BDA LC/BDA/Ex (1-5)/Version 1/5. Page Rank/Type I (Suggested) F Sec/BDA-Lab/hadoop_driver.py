import os

input_file = "/home/cloudera/BDA-Lab/input.txt"
mapper_file = "/home/cloudera/BDA-Lab/mapper.py"
reducer_file = "/home/cloudera/BDA-Lab/reducer.py"
hdfs_input = "/user/cloudera/input.txt"
hdfs_output_base = "/user/cloudera/laboutput"
hadoop_streaming_jar = "/usr/lib/hadoop-0.20-mapreduce/contrib/streaming/hadoop-streaming-2.6.0-mr1-cdh5.4.2.jar"
max_iter = 4

# Step 1: Clean HDFS and put input
os.system("hadoop fs -rm %s" % hdfs_input)
os.system("hadoop fs -rm -r %s*" % hdfs_output_base)
os.system("hadoop fs -put %s %s" % (input_file, hdfs_input))

for i in range(1, max_iter+1):
    hdfs_output = "%s_iter%d" % (hdfs_output_base, i)
    os.system("hadoop fs -rm -r %s" % hdfs_output)

    print "="*32
    print "Running Hadoop PageRank Iteration %d" % i
    print "="*32

    # Step 2: Run Hadoop Streaming job
    os.system(
        "hadoop jar %s "
        "-files %s,%s "
        "-mapper 'python mapper.py' "
        "-reducer 'python reducer.py' "
        "-input %s "
        "-output %s"
        % (hadoop_streaming_jar, mapper_file, reducer_file, hdfs_input, hdfs_output)
    )

    # Step 3: Show output and prepare for next iteration
    os.system("hadoop fs -cat %s/part-00000 > iteration_%d.txt" % (hdfs_output, i))

    # Use output as input for next iteration
    os.system("hadoop fs -rm %s" % hdfs_input)
    os.system("hadoop fs -put iteration_%d.txt %s" % (i, hdfs_input))

print "="*32
print "Hadoop PageRank Simulation Completed"
print "="*32
