import filecmp
import os
import re
import multiprocessing as mp
# from compiler import interpret
from compiler_f import run
noTC = {'1': 10,'2': 10,'3': 10,'4': 10,'5': 10,'6': 10,'7': 10,'8' : 10,'9' : 10,'10' : 10}

def score(code, qn_no, pno):
    count = 0
    # inputPath = './E-Contest/app/evaluation/input/qn'+qn_no
    inputPath = './evaluation/input/qn' + qn_no
    
    # Check if the input directory exists
    if not os.path.exists(inputPath):
        return "Input directory does not exist"

    for filename in os.listdir(inputPath):
        if 'tc' in filename:
            fno = re.sub('[^0-9]+', '', filename)
            # outputfilePath = './E-Contest/app/evaluation/output' + pno + '.txt'
            outputfilePath = f'./evaluation/output{int(pno) % 3}.txt'

            # Check if the output directory exists
            print(outputfilePath)
            if not os.path.exists(outputfilePath):
                return "Output directory does not exist"
                
            with open(outputfilePath, 'w+') as mfile:
                count += 1
                inpfilePath = inputPath + '/' + filename
                
                # Check if input file exists and is not empty
                if not os.path.exists(inpfilePath) or os.path.getsize(inpfilePath) == 0:
                    return f"Input file {filename} is empty or doesn't exist"

                Q = mp.Queue()
                prc = mp.Process(target=run, args=(code, inpfilePath, outputfilePath, Q))
                prc.daemon = True
                prc.start()

                # Timeout mechanism to prevent hanging indefinitely
                try:
                    Message = Q.get(timeout=10)  # Timeout after 10 seconds
                except mp.Queue.Empty:
                    prc.terminate()
                    prc.join()
                    mfile.close()
                    return 'TIME LIMIT EXCEEDED'

                if Message == "ANSWER WRITTEN":
                    expected_output_file = './evaluation/expected_output/qn' + qn_no + '/output-' + str(fno) + '.txt'
                    
                    # Check if expected output file exists and is not empty
                    if not os.path.exists(expected_output_file) or os.path.getsize(expected_output_file) == 0:
                        return f"Expected output file {expected_output_file} is missing or empty"
                    
                    if filecmp.cmp(outputfilePath, expected_output_file):
                        pass  # Correct answer
                    else:
                        return 'WRONG ANSWER'
                else:
                    mfile.close()
                    return Message  # Error message from the process

    return 'CORRECT ANSWER'