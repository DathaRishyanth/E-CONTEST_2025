with open('./evaluation/expected_output/qn1/output-2.txt', 'w') as f:
    char = '1'
    # char = str(char)
    char1 = f.write(char)
    # char = int(char)
    # # char = str(char)
    print(type(char1))
    print(char1)
with open('./evaluation/expected_output/qn1/output-2.txt', 'r') as f:
    # char = 1
    # char = str(char)
    char2 = f.read()
    # char2 = int(char)
    # char = str(char)
    print(type(char))
    print(char)
if(char1 == char2):
    print('*')