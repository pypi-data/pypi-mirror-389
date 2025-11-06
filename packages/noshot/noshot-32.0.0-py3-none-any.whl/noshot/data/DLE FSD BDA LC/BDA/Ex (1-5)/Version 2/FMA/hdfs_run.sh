#!/bin/bash
echo "============================================"
echo "Hadoop MapReduce Runner - Cloudera"
echo "Universal Exercise Runner"
echo "============================================"
echo

# Set variables
JOB_NAME="${1:-MapReduceJob}"
INPUT_DIR="/user/cloudera/input"
OUTPUT_DIR1="/user/cloudera/output1"
OUTPUT_DIR2="/user/cloudera/output2"
PYTHON_PATH="python"
JAR_FILE="/usr/lib/hadoop-mapreduce/hadoop-streaming.jar"

echo "[INFO] Starting job: $JOB_NAME"
echo "[INFO] Using Python: $(which $PYTHON_PATH 2>/dev/null || echo 'python')"
echo

# Check if required files exist
echo "[CHECK] Verifying required files..."
echo "Command: ls -la *.py"
ls -la *.py
echo

if [ ! -f "mapper.py" ] && [ ! -f "mapper1.py" ]; then
    echo "ERROR: No mapper files found! (mapper.py or mapper1.py)"
    exit 1
fi

if [ ! -f "reducer.py" ] && [ ! -f "reducer1.py" ]; then
    echo "ERROR: No reducer files found! (reducer.py or reducer1.py)"
    exit 1
fi

# Find input file (data.csv or data.txt)
INPUT_FILE=""
echo "Command: ls -la data.*"
ls -la data.* 2>/dev/null || echo "No data files found yet"
echo

if [ -f "data.csv" ]; then
    INPUT_FILE="data.csv"
    echo "[INFO] Found input file: data.csv"
elif [ -f "data.txt" ]; then
    INPUT_FILE="data.txt"
    echo "[INFO] Found input file: data.txt"
else
    echo "ERROR: No data.csv or data.txt found!"
    exit 1
fi

echo "[SUCCESS] All required files found!"
echo

# Detect multiple mappers/reducers
NUM_MAPPERS=0
NUM_REDUCERS=0

# Check for multiple mappers
if [ -f "mapper1.py" ] && [ -f "mapper2.py" ]; then
    NUM_MAPPERS=2
    echo "[INFO] Detected 2 mappers: mapper1.py, mapper2.py"
elif [ -f "mapper.py" ]; then
    NUM_MAPPERS=1
    echo "[INFO] Detected 1 mapper: mapper.py"
fi

# Check for multiple reducers
if [ -f "reducer1.py" ] && [ -f "reducer2.py" ]; then
    NUM_REDUCERS=2
    echo "[INFO] Detected 2 reducers: reducer1.py, reducer2.py"
elif [ -f "reducer.py" ]; then
    NUM_REDUCERS=1
    echo "[INFO] Detected 1 reducer: reducer.py"
fi

echo

# Step 0: Local testing of mappers and reducers
echo "[STEP 0] Local testing of mappers and reducers..."
echo

if [ $NUM_MAPPERS -eq 2 ] && [ $NUM_REDUCERS -eq 2 ]; then
    echo "Testing mapper1: cat $INPUT_FILE | $PYTHON_PATH mapper1.py | head -5"
    cat $INPUT_FILE | $PYTHON_PATH mapper1.py | head -5
    echo
    
    echo "Testing mapper2: cat $INPUT_FILE | $PYTHON_PATH mapper2.py | head -5"
    cat $INPUT_FILE | $PYTHON_PATH mapper2.py | head -5
    echo
    
    echo "Testing mapper1 -> reducer1: cat $INPUT_FILE | $PYTHON_PATH mapper1.py | sort | $PYTHON_PATH reducer1.py | head -5"
    cat $INPUT_FILE | $PYTHON_PATH mapper1.py | sort | $PYTHON_PATH reducer1.py | head -5
    echo
    
    echo "Testing mapper2 -> reducer2: cat $INPUT_FILE | $PYTHON_PATH mapper2.py | sort | $PYTHON_PATH reducer2.py | head -5"
    cat $INPUT_FILE | $PYTHON_PATH mapper2.py | sort | $PYTHON_PATH reducer2.py | head -5
    echo

elif [ $NUM_MAPPERS -eq 2 ] && [ $NUM_REDUCERS -eq 1 ]; then
    echo "Testing mapper1: cat $INPUT_FILE | $PYTHON_PATH mapper1.py | head -5"
    cat $INPUT_FILE | $PYTHON_PATH mapper1.py | head -5
    echo
    
    echo "Testing mapper2: cat $INPUT_FILE | $PYTHON_PATH mapper2.py | head -5"
    cat $INPUT_FILE | $PYTHON_PATH mapper2.py | head -5
    echo
    
    echo "Testing mapper1 -> reducer: cat $INPUT_FILE | $PYTHON_PATH mapper1.py | sort | $PYTHON_PATH reducer.py | head -5"
    cat $INPUT_FILE | $PYTHON_PATH mapper1.py | sort | $PYTHON_PATH reducer.py | head -5
    echo

else
    echo "Testing mapper: cat $INPUT_FILE | $PYTHON_PATH mapper.py | head -5"
    cat $INPUT_FILE | $PYTHON_PATH mapper.py | head -5
    echo
    
    echo "Testing mapper -> reducer: cat $INPUT_FILE | $PYTHON_PATH mapper.py | sort | $PYTHON_PATH reducer.py | head -5"
    cat $INPUT_FILE | $PYTHON_PATH mapper.py | sort | $PYTHON_PATH reducer.py | head -5
    echo
fi

read -p "Press [Enter] to continue to HDFS operations or [Ctrl+C] to stop..."
echo

# Step 1: Prepare HDFS
echo "[STEP 1] Preparing HDFS directories..."
echo "Command: hadoop fs -mkdir -p $INPUT_DIR"
hadoop fs -mkdir -p $INPUT_DIR 2>/dev/null
echo "Created/verified input directory: $INPUT_DIR"
echo "Command: hadoop fs -ls /user/cloudera/"
hadoop fs -ls /user/cloudera/ 2>/dev/null
echo

# Step 2: Upload data
echo "[STEP 2] Uploading input data..."
echo "Command: hadoop fs -put -f $INPUT_FILE $INPUT_DIR/"
hadoop fs -put -f $INPUT_FILE $INPUT_DIR/
echo "Uploaded $INPUT_FILE to HDFS"
echo "Command: hadoop fs -ls $INPUT_DIR"
hadoop fs -ls $INPUT_DIR 2>/dev/null
echo

# Step 3: Clean previous outputs
echo "[STEP 3] Cleaning previous outputs..."
echo "Command: hadoop fs -rm -r -f $OUTPUT_DIR1"
hadoop fs -rm -r -f $OUTPUT_DIR1 2>/dev/null
echo "Command: hadoop fs -rm -r -f $OUTPUT_DIR2"
hadoop fs -rm -r -f $OUTPUT_DIR2 2>/dev/null
echo "Removed previous output directories"
echo

# Step 4: Run MapReduce jobs sequentially
echo "[STEP 4] Running Hadoop Streaming Jobs Sequentially..."

if [ $NUM_MAPPERS -eq 2 ] && [ $NUM_REDUCERS -eq 2 ]; then
    # First Job: mapper1 + reducer1
    echo "[JOB 1] Running mapper1 + reducer1..."
    echo "Command: hadoop jar $JAR_FILE \\"
    echo "  -files mapper1.py,reducer1.py \\"
    echo "  -mapper \"$PYTHON_PATH mapper1.py\" \\"
    echo "  -reducer \"$PYTHON_PATH reducer1.py\" \\"
    echo "  -input $INPUT_DIR \\"
    echo "  -output $OUTPUT_DIR1"
    echo
    
    hadoop jar $JAR_FILE \
      -files mapper1.py,reducer1.py \
      -mapper "$PYTHON_PATH mapper1.py" \
      -reducer "$PYTHON_PATH reducer1.py" \
      -input $INPUT_DIR \
      -output $OUTPUT_DIR1

    JOB1_EXIT_CODE=$?
    echo "[JOB 1] Completed with exit code: $JOB1_EXIT_CODE"
    echo

    if [ $JOB1_EXIT_CODE -eq 0 ]; then
        # Second Job: mapper2 + reducer2 (using output from first job as input)
        echo "[JOB 2] Running mapper2 + reducer2..."
        echo "Command: hadoop jar $JAR_FILE \\"
        echo "  -files mapper2.py,reducer2.py \\"
        echo "  -mapper \"$PYTHON_PATH mapper2.py\" \\"
        echo "  -reducer \"$PYTHON_PATH reducer2.py\" \\"
        echo "  -input $OUTPUT_DIR1 \\"
        echo "  -output $OUTPUT_DIR2"
        echo
        
        hadoop jar $JAR_FILE \
          -files mapper2.py,reducer2.py \
          -mapper "$PYTHON_PATH mapper2.py" \
          -reducer "$PYTHON_PATH reducer2.py" \
          -input $OUTPUT_DIR1 \
          -output $OUTPUT_DIR2

        JOB2_EXIT_CODE=$?
        echo "[JOB 2] Completed with exit code: $JOB2_EXIT_CODE"
        echo
        
        # Set final exit code
        JOB_EXIT_CODE=$JOB2_EXIT_CODE
        FINAL_OUTPUT_DIR=$OUTPUT_DIR2
    else
        JOB_EXIT_CODE=$JOB1_EXIT_CODE
        FINAL_OUTPUT_DIR=$OUTPUT_DIR1
    fi

elif [ $NUM_MAPPERS -eq 2 ] && [ $NUM_REDUCERS -eq 1 ]; then
    # First Job: mapper1 + reducer
    echo "[JOB 1] Running mapper1 + reducer..."
    echo "Command: hadoop jar $JAR_FILE \\"
    echo "  -files mapper1.py,reducer.py \\"
    echo "  -mapper \"$PYTHON_PATH mapper1.py\" \\"
    echo "  -reducer \"$PYTHON_PATH reducer.py\" \\"
    echo "  -input $INPUT_DIR \\"
    echo "  -output $OUTPUT_DIR1"
    echo
    
    hadoop jar $JAR_FILE \
      -files mapper1.py,reducer.py \
      -mapper "$PYTHON_PATH mapper1.py" \
      -reducer "$PYTHON_PATH reducer.py" \
      -input $INPUT_DIR \
      -output $OUTPUT_DIR1

    JOB1_EXIT_CODE=$?
    echo "[JOB 1] Completed with exit code: $JOB1_EXIT_CODE"
    echo

    if [ $JOB1_EXIT_CODE -eq 0 ]; then
        # Second Job: mapper2 + reducer (using output from first job as input)
        echo "[JOB 2] Running mapper2 + reducer..."
        echo "Command: hadoop jar $JAR_FILE \\"
        echo "  -files mapper2.py,reducer.py \\"
        echo "  -mapper \"$PYTHON_PATH mapper2.py\" \\"
        echo "  -reducer \"$PYTHON_PATH reducer.py\" \\"
        echo "  -input $OUTPUT_DIR1 \\"
        echo "  -output $OUTPUT_DIR2"
        echo
        
        hadoop jar $JAR_FILE \
          -files mapper2.py,reducer.py \
          -mapper "$PYTHON_PATH mapper2.py" \
          -reducer "$PYTHON_PATH reducer.py" \
          -input $OUTPUT_DIR1 \
          -output $OUTPUT_DIR2

        JOB2_EXIT_CODE=$?
        echo "[JOB 2] Completed with exit code: $JOB2_EXIT_CODE"
        echo
        
        JOB_EXIT_CODE=$JOB2_EXIT_CODE
        FINAL_OUTPUT_DIR=$OUTPUT_DIR2
    else
        JOB_EXIT_CODE=$JOB1_EXIT_CODE
        FINAL_OUTPUT_DIR=$OUTPUT_DIR1
    fi

else
    # Single Job: mapper + reducer
    echo "[JOB] Running mapper + reducer..."
    echo "Command: hadoop jar $JAR_FILE \\"
    echo "  -files mapper.py,reducer.py \\"
    echo "  -mapper \"$PYTHON_PATH mapper.py\" \\"
    echo "  -reducer \"$PYTHON_PATH reducer.py\" \\"
    echo "  -input $INPUT_DIR \\"
    echo "  -output $OUTPUT_DIR1"
    echo
    
    hadoop jar $JAR_FILE \
      -files mapper.py,reducer.py \
      -mapper "$PYTHON_PATH mapper.py" \
      -reducer "$PYTHON_PATH reducer.py" \
      -input $INPUT_DIR \
      -output $OUTPUT_DIR1

    JOB_EXIT_CODE=$?
    echo "[JOB] Completed with exit code: $JOB_EXIT_CODE"
    echo
    FINAL_OUTPUT_DIR=$OUTPUT_DIR1
fi

echo
echo "[STEP 5] Final job completed with exit code: $JOB_EXIT_CODE"
echo

# Step 6: Show results
if [ $JOB_EXIT_CODE -eq 0 ]; then
    echo "[STEP 6] Displaying results from $FINAL_OUTPUT_DIR..."
    echo "Command: hadoop fs -ls $FINAL_OUTPUT_DIR"
    hadoop fs -ls $FINAL_OUTPUT_DIR 2>/dev/null
    echo
    echo "First 10 lines of each output file:"
    for file in $(hadoop fs -ls $FINAL_OUTPUT_DIR | grep part | awk '{print $8}'); do
        echo "Command: hadoop fs -cat $file | head -10"
        echo "=== $file ==="
        hadoop fs -cat $file 2>/dev/null | head -10
        echo
    done
    echo "Command: hadoop fs -cat $FINAL_OUTPUT_DIR/part-* | wc -l"
    echo "Total output lines:"
    hadoop fs -cat $FINAL_OUTPUT_DIR/part-* 2>/dev/null | wc -l
else
    echo "[ERROR] Job failed! Check Hadoop logs for details."
fi

echo
echo "============================================"
echo "Job execution completed!"
echo "Final output location: hdfs://$FINAL_OUTPUT_DIR"
echo "============================================"