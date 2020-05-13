from pathlib import Path
import os
import io
import re
import glob
import operator

###
# Version 0.1
##

def main():    

    #col_heading = ['F01','F02','F03','F04','F05','F06','F07','F08','F09','F10','F11','F12','F13','F14','F15','F16','F17','F18','F19','F20','F21','F22','F23','F24','F25','F26','F27','F28','F29','F30','F31','F32','F33','F34','REMARK']
    col_heading = ['BILLING_PERIOD', 'AWB_DATE', 'TXN_TYPE', 'AGENT_CODE', 'AWB_NBR', 'ORIGIN', 'DESTINATION', 'WEIGHT', 'AF_RATE', 'ADJ_WEIGHT_CHARGE', 'CARRIER_DUE', 'NET_DUE', 'CURRENCY', 'KE_CCA_CODE', 'WEIGHT_CHARGE_ORIG', 'VALUATION_CHARGE', 'AGENT_DUE', 'COMMISSION', 'SALES_INCENTIVE', 'BILLING FILENAME']

    file_list = glob.glob('**/*.txt')
    file_list.extend(glob.glob('**/*.bil'))
    file_list.extend(glob.glob('**/*.fil'))
    file_list.extend(glob.glob('*.txt'))
    file_list.extend(glob.glob('*.bil'))
    file_list.extend(glob.glob('*.fil'))
   
    print(f"Found {len(file_list)} CNS Billing files")
    response = input('Create separate csv files for each?\nPress <Enter> for merged report. ')
    if re.match('^y',response.lower()):
        merge_output = False
    else:
        merge_output = True
        output_filename = 'CASS_BILLED.csv'
        if os.path.isfile(output_filename):
            os.unlink('CASS_BILLED.csv')
        out_file_handle = open('CASS_BILLED.csv','a')
        out_file_handle.write(','.join(col_heading))
        out_file_handle.write("\n")

    for a_file in file_list:

        in_file_handle = open(a_file,'r')

        output_buffer = []
        AWM_record = []
        CCA_record = []

        for line in in_file_handle:
            line.strip()
            #print(line)

            # ALS RECORDS - FILE HEADERS  3 2 11 3 6 6 6 2 211
            #[CD]C[OR] RECORD - {3}{1}{1}{3}{8}{2}{3}{11} {6}{3}{11}{6}{1}{12}{1}{12} {1}{12}{1}{12}{1}{12}{12}{12} {12}{12}{1}{1}{7}{3}{67}
            if re.match('^ALS', line):
                #print("Found header>"+line)
                record_id = line[0:3]
                #cass_area_code = line[3:5]
                #filler0 = line[5:16]
                #airline_number = line[16:19]
                period_start_date = '20' + line[19:21] + '-' + line[21:23] + '-' + line[23:25] #YYMMDD
                period_ref = (int(line[19:21]) * 100) + (int(line[21:23]) - 1) * 2 + (1 if int(line[23:25]) < 16 else 2)
                #period_end_date = '20' + line[25:27] + '-' + line[27:29] + '-' + line[29:31] #YYMMDD
                #file_nbr = line[31:33]
                #filler1 = line[31:]

                #output_buffer.append("'"+",'".join([record_id,cass_area_code,airline_number,payment_collection_date_start,payment_collection_date_end,date_of_disbursement,file_number,date_of_billing,reserved]))
                #print(len(output_buffer))

                if False: #debugging output
                    print(record_id)
                    #print(cass_area_code)
                    #print(airline_number)
                    print(period_start_date)
                    #print(period_end_date)
                    #print(disbursement_date)
                    #print(file_nbr)
                    #print(filler1)
                    input('<PAUSE>')

            # AWM RECORDS - 3 1 1 11 3 8 2 3 1 2 3 6 7 1 3 12 12 12 12 12 12 12 12 4 12 1 12 6 14 11 12 12 14 1
            elif re.match('^AWM', line):
                record_id = line[0:3]
                agent_code = '\'' + line[5:16]
                awb_serial_number = int(line[16:27])
                origin = line[29:32]
                #awb_use_indicator = line[32:33]
                destination = line[35:38]
                weight = float(line[44:51])/10
                currency_code = line[52:55]
                weight_charge = float(line[55:67])/100
                valuation_charge = float(line[67:79])/100
                carrier_due = float(line[79:91])/100
                agent_due = float(line[91:103])/100
                commission = float(line[155:167])/100
                incentive = float(line[168:180])/100
                awb_acceptance_date = '20' + line[180:182] + '-' + line[182:184] + '-' + line[184:186]
                agents_reference_data = str(line[186:200]).replace(' ','')
                incentive_sign = line[249:250]
                if incentive_sign == '-':
                    incentive *= -1

                rvsd_weight_charge = round(weight_charge + valuation_charge - agent_due - commission - incentive, 2)
                net_due = round(rvsd_weight_charge + carrier_due, 2)

                if abs(round(rvsd_weight_charge / weight * 100, 4) - (rvsd_weight_charge / weight * 100)) > .001:
                    rate = rvsd_weight_charge
#                    print(f"A{awb_serial_number}:{rvsd_weight_charge/weight}")
                elif rvsd_weight_charge <= 600.00 and int(weight) < 45 and int(rvsd_weight_charge * 100) % 2500 == 0:
                    rate = rvsd_weight_charge
#                    print(f"B{awb_serial_number}:{rvsd_weight_charge/weight}")
                elif rvsd_weight_charge == 65.00 and int(weight) < 100:
                    rate = rvsd_weight_charge
                else:
                    rate = round(rvsd_weight_charge / weight, 2)
#                    print(f"C{awb_serial_number}:{rvsd_weight_charge/weight}")

                #print(f"rate:{rate}")
                #input('<PAUSE>')
#                if awb_serial_number == 18047590174:
#                    print(f"{abs(round(rvsd_weight_charge / weight * 100, 4) - (rvsd_weight_charge / weight * 100))}")
#                    input('<PAUSE>')
                record_id_sort_priority = 1
                AWM_record = [record_id_sort_priority, period_ref, awb_acceptance_date, record_id, agent_code, awb_serial_number, origin, destination, weight, rate, rvsd_weight_charge, carrier_due, net_due, currency_code, agents_reference_data, weight_charge, valuation_charge, agent_due, commission, incentive, a_file]

                if False: #debugging output
                    print_array(AWM_record)
                    print_array([record_id, awb_serial_number, weight_charge, carrier_due, valuation_charge, agent_due, commission, incentive, rvsd_weight_charge, net_due])
                    input('<PAUSE>')

                output_buffer.append(AWM_record)


            #[CD]C[OR] RECORD - 3 1 1 3 8 2 3 11 6 3 11 6 1 12 1 12 1 12 1 12 1 12 12 12 12 12 1 1 7 3 67
            elif re.match('^[CDE]C[OR]', line):
                #print ("Found cca>"+line)
                record_id = line[0:3]  #FIELD 1
                awb_serial_number = int(line[5:16])  #FIELD 4&5
                origin = line[18:21] #FIELD 7
                agent_code = '\'' + line[21:32] #FIELD 8
                cca_number = str(line[32:38]) #F9
                currency_code = line[38:41] #F10
                awb_execution_date = '20' + line[52:54] + '-' + line[54:56] + '-' + line[56:58]
                weight_charge_sign = line[58:59]
                weight_charge = float(line[59:71])/100 #F14
                if weight_charge_sign == 'C':
                    weight_charge = round(weight_charge * -1, 2) + 0.0
                valuation_charge_sign = line[71:72] #F16
                valuation_charge = float(line[72:84])/100
                if valuation_charge_sign == 'C':
                    valuation_charge = round(valuation_charge * -1, 2) + 0.0
                agent_due_sign = line[97:98]
                agent_due = float(line[98:110])/100 #F20
                if agent_due_sign == 'C':
                    agent_due = round(agent_due * -1, 2) + 0.0
                carrier_due_sign = line[110:111]
                carrier_due = float(line[111:123])/100 #F22
                if carrier_due_sign == 'C':
                    carrier_due = round(carrier_due * -1, 2) + 0.0
                commission = float(line[135:147])/100
                incentive = float(line[159:171])/100
                incentive_sign = line[171:172]
                if incentive_sign == '-':
                    incentive *= -1 + 0.0

                weight = float(line[173:180])/10
                destination = line[180:183]

                rvsd_weight_charge = round(weight_charge + valuation_charge - agent_due - commission - incentive, 2)
                net_due = round(rvsd_weight_charge + carrier_due, 2)
                if re.search('O$', record_id):
                    net_due *= -1

                if abs(round(rvsd_weight_charge / weight * 100, 4) - (rvsd_weight_charge / weight * 100)) > .001:
                    rate = rvsd_weight_charge
                elif rvsd_weight_charge <= 600.00 and int(weight) < 45 and int(rvsd_weight_charge * 100) % 2500 == 0:
                    rate = rvsd_weight_charge
                elif rvsd_weight_charge == 65.00 and int(weight) < 100:
                    rate = rvsd_weight_charge
                else:
                    rate = round(rvsd_weight_charge / weight, 2)

                record_id_sort_priority = 2
                CCA_record = [record_id_sort_priority, period_ref, awb_execution_date, record_id, agent_code, awb_serial_number, origin, destination, weight, rate, rvsd_weight_charge, carrier_due, net_due, currency_code, cca_number, weight_charge, valuation_charge, agent_due, commission, incentive, a_file]

                if False: #debugging output
                    print_array(CCA_record)
                    print_array([record_id,weight_charge,valuation_charge,agent_due,carrier_due,commission,incentive])
                    input('<PAUSE>')

                output_buffer.append(CCA_record)

            else:
                pass

        in_file_handle.close()

        if merge_output == False:
            new_csv_filename = a_file[0:-4] + '.csv'
            out_file_handle = open(new_csv_filename,'w')
            out_file_handle.write(','.join(col_heading))
            out_file_handle.write("\n")

        #sort the file by this order:
        output_buffer.sort(key= operator.itemgetter(3), reverse=True) #KE_CCA_CODE
        output_buffer.sort(key= operator.itemgetter(14)) #KE_CCA_CODE
        output_buffer.sort(key= operator.itemgetter(5)) #AWB_NBR
        output_buffer.sort(key= operator.itemgetter(4)) #AGENT_CODE
        output_buffer.sort(key= operator.itemgetter(0)) #record_id_sort_priority
        output_buffer.sort(key= operator.itemgetter(1)) #BILLING_PERIOD


        for line in output_buffer:
            line.pop(0) #dequeue record_id_sort_priority from the record. Needed only to sorting order
            for i in range(len(line)):
                if i > 0:
                    out_file_handle.write(','+str(line[i]))
                else:
                    out_file_handle.write(str(line[i]))
            out_file_handle.write("\n")

        if merge_output == False:
            out_file_handle.close()

    #read in all files
    out_file_handle.close()

def print_array(arr1):
    print('[', end='')
    for i in range(len(arr1)):
        if i > 0:
            print(','+str(arr1[i]), end='')
        else:
            print(arr1[i], end='')

    print(']')
    
    return 0

if __name__ == '__main__':
    main()