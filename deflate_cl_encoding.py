import bitstring
import numpy as np

verbose = 1

def cl_encoding(bytestring):
    """
    this is a run length encoder used to encode the code lengths
    that we generated in deflate

    every symbol is coded in 5-bits fixed
    if we are coding a repeat case, there will be
    following offset bits as explained below

    non-zero run length are limited to 6 repeats.
    zero run lengths are limited to 138 repeats.

    16:
        followed by a 2-bit value x
        repeat the previous length x+3 times
        2 bits-> 3
        3 + 3 = 6
        minimum length needs to be 0 + 3 = 3
        3 <= len <= 6

    17:
        followed by a 3-bit value x
        repeat a zero length x+3 times
        3 bits -> 7
        7 + 3 = 10
        minimum length needs to be 0 + 3 = 3
        3 <= len <= 10

    18:
        followed by a 7-bit value z
        repeat a zero length x+11 times
        7 bits -> 27
        127 + 11 = 138
        minimum length needs to be 0 + 11 = 11
        11 <= len <= 138

    """

    encoded = ''

    symbols = []

    cl_counts = len(bytestring)

    i = 0

    while i < cl_counts:

        length = 0

        found_something = False
        use_case = 0

        current = bytestring[i]

        if i == cl_counts - 1:
            encoded = encoded + bitstring.BitArray(f"uint5={current}").bin
            if verbose: print(f"{current}")
            symbols.append(current)
            break

        while True:

            next = bytestring[i + 1 + length]

            if (current == next):

                length = length + 1

                found_something = True

                if (i + length) == cl_counts - 1:
                    break

                if current == 0:

                    if length + 1 == 138:
                        break
                else:
                    if length == 6:
                        break


            else:
                break

        if found_something:

            #if verbose:  print(f"found that {bytestring[i]} repeats {length} times.")

            """
            we have found a run length
            now we need to see if the length is suitable for our case
            """

            if (current == 0):
                if 3 <= length + 1 <= 10:
                    use_case = 17

                elif 11 <= length + 1 <= 138:
                    use_case = 18

            else:
                if 3 <= length <= 6:
                    use_case = 16


        if found_something and use_case != 0:

            i = i + length + 1


            if current == 0:

                encoded = encoded + bitstring.BitArray(f"uint5={use_case}").bin

                if verbose: print(f"repeat a zero length {length + 1} times, use_case:{use_case}")
                symbols.append(use_case)


                if (use_case == 17):
                    rep_offset = (length + 1) - 3
                    encoded = encoded + bitstring.BitArray(f"uint3={rep_offset}").bin

                elif (use_case == 18):
                    rep_offset = (length + 1) - 11
                    encoded = encoded + bitstring.BitArray(f"uint7={rep_offset}").bin

            else:
                encoded = encoded + bitstring.BitArray(f"uint5={current}").bin
                if verbose: print(f"{current}")
                symbols.append(current)


                encoded = encoded + bitstring.BitArray(f"uint5={use_case}").bin

                if verbose: print(f"repeat the previous length {length} times, use_case:{use_case}")
                symbols.append(use_case)


                rep_offset = max(0, length - 3)
                encoded = encoded + bitstring.BitArray(f"uint2={rep_offset}").bin




        else:
            encoded = encoded + bitstring.BitArray(f"uint5={current}").bin
            if verbose: print(f"{current}")
            symbols.append(current)

            i = i + 1


    return [encoded, symbols]


def cl_decoding(bitstream):

    total_used_bits = 0

    decoded = ''

    while total_used_bits < len(bitstream):

        bit_chunk = bitstream[total_used_bits: total_used_bits + 5]
        total_used_bits = total_used_bits + 5

        encoded = int(bit_chunk, 2)


        if encoded == 16:
            reps = bitstream[total_used_bits: total_used_bits + 2]
            total_used_bits = total_used_bits + 2
            reps = 3 + int(reps, 2)
            decoded = decoded + reps * decoded[-5:]


        elif encoded == 17:
            reps = bitstream[total_used_bits: total_used_bits + 3]
            total_used_bits = total_used_bits + 3
            reps = 3 + int(reps, 2)
            decoded = decoded + reps * '00000'


        elif encoded == 18:
            reps = bitstream[total_used_bits: total_used_bits + 7]
            total_used_bits = total_used_bits + 7
            reps = 11 + int(reps, 2)
            decoded = decoded + reps * '00000'


        else:
            decoded = decoded + bit_chunk

    chunks = [int(decoded[i:i + 5],2) for i in range(0, len(decoded), 5)]

    return chunks



def apply_huffman_codes_to_encoded_cl_bitstream(bitstream, codes):

    total_used_bits = 0

    decoded = ''

    while total_used_bits < len(bitstream):

        five_bit_chunk = bitstream[total_used_bits: total_used_bits + 5]
        total_used_bits = total_used_bits + 5

        decoded = decoded + codes[(9 - 5) * '0' + five_bit_chunk]


        symbol = int(five_bit_chunk, 2)

        if symbol == 16:
            decoded = decoded + bitstream[total_used_bits: total_used_bits + 2]
            total_used_bits = total_used_bits + 2


        elif symbol == 17:
            decoded = decoded + bitstream[total_used_bits: total_used_bits + 3]
            total_used_bits = total_used_bits + 3


        elif symbol == 18:
            decoded = decoded + bitstream[total_used_bits: total_used_bits + 7]
            total_used_bits = total_used_bits + 7


    return decoded




global left_over
global fixed_width_memory
global encoded_mem_width

fixed_width_memory = []
left_over = ''
encoded_mem_width = 2


def write_to_fixed_width_mem(input_bits, bits_count, last_load=False):
    """
    we keep a left-over (if nesacery)
    and we use it together with the incoming bits
    """

    global left_over
    global fixed_width_memory
    global encoded_mem_width



    remaining_bits = bits_count

    counter = 0

    starting_index = 0

    allowed_to_write = True

    if left_over != '':

        if len(left_over) + remaining_bits >= encoded_mem_width:
            fixed_width_memory.append(left_over + input_bits[:encoded_mem_width-len(left_over)])

            remaining_bits = remaining_bits - (encoded_mem_width-len(left_over))
            starting_index = encoded_mem_width-len(left_over)
            left_over = ''


        else:
            left_over = left_over + input_bits
            allowed_to_write = False


    if allowed_to_write:

        while remaining_bits >= encoded_mem_width:

            # store the first (most left) chunk of the input
            fixed_width_memory.append(
                input_bits[
                    starting_index + counter * encoded_mem_width :
                    starting_index +  (counter + 1) * encoded_mem_width
                ]
            )

            remaining_bits = remaining_bits - encoded_mem_width
            counter = counter +1

        if remaining_bits > 0:
            left_over = input_bits[-remaining_bits:]


    if last_load:
        if left_over != '':
            fixed_width_memory.append(left_over)
            left_over = ''


    return





def verify_verilog_output_bitstream():

    with open("C:\\Users\\jahan\\Desktop\\verilog\\deflate\\clcoding\\dumps\\G6_output_file_general.txt", 'r') as f:
        lines = f.read().split('\n')[:-1]
        hlit = int(lines[0], 2)


    with open("C:\\Users\\jahan\\Desktop\\verilog\\deflate\\writer\\dumps\\H_output_file_general.txt", 'r') as f:
        lines = f.read().split('\n')[:-1]
        last_entry_bit_counts = int(lines[0], 2)



    encoded_mem_width = 8


    cls_file = open("../verilog/deflate/clcoding/input_huffman_codes.txt", "r")
    cls_data = cls_file.read().split('\n')[:-1]
    cls = [int(x[9:21], 2) for x in cls_data][:-hlit]

    verilog_symbols_data = open("../verilog/deflate/clcoding/dumps/G5_output_file_symbols_mem.txt", "r")
    symbols_data = verilog_symbols_data.read().split('\n')[:-1]
    symbols_verilog = [int(x,2) for x in symbols_data]



    with open("../verilog/deflate/writer/dumps/H4_output_file_bit_stream_mem.txt", "r") as my_file:
        verilog_output_bits = my_file.read().split('\n')

    verilog_output_bits = ''.join(verilog_output_bits[:-1])

    if last_entry_bit_counts > 0:
        verilog_output_bits = verilog_output_bits[:-(encoded_mem_width - last_entry_bit_counts)]


    rec = cl_decoding(verilog_output_bits)


    encoded, symbols = cl_encoding(cls)
    assert symbols==symbols_verilog
    assert cls == rec


    df = 3



if __name__ == '__main__':

    verify_verilog_output_bitstream()

    print("all good.")

    exit()

    data = [0,0,0,0,0,0,0,1,2,3,3,3,3,3]

    encoded, symbols = cl_encoding(data)
    decoded = cl_decoding(encoded)


    print(decoded)

    assert data == decoded, '!!!!!!!!!!'



    data = 'it does all the cutting and appendings required to fit the data in the memory.C:/Program Files/JetBrains/PyCharm Community Edition 2022.3.1/plugins/python-ce/helpers/pydev/pydevd.py" --multiprocess --qt-support=auto --client 127.0.0.1 --port 5553'

    pointer = 0
    while pointer < len(data):
        length = 1 + int(15 * np.random.uniform())

        chunk = data[pointer: pointer + length]
        pointer += length

        write_to_fixed_width_mem(chunk, length)
        s3=4

        assert ('').join(fixed_width_memory) == data[:len(('').join(fixed_width_memory))]



