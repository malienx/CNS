from pathlib import Path
import os
import io
import re
import glob

###
# Version 3.0
##

def main():    
    #readin_buffer = in_file_handle.readlines()

    for filename in glob.glob('180*.fil'):
        if os.path.isfile(filename):
            filename_as_str = str(filename)
            new_filename = filename_as_str[0:-4] + '.txt'
            #print(new_filename)
            os.replace(filename, os.path.join(os.getcwd(),new_filename))

    wanted_file_list = glob.glob('**/180*.txt', recursive=True)
#    print(len(wanted_file_list))
#    input('<PAUSE>')

    col_heading = ['CASS_AREA_CODE','COLLECT_DATE','DEPOSIT_DATE','AWB_DATE','IATA_NBR','AWB_NBR','ORIG','DEST',
                    'WT','PAID_AMT','TXN_TYPE','PERIOD','CURRENCY','ADJUSTMENT_REASON_CODE','ADJUSTMENT_DESCRIPTION','CCA_NBR']


    print(f"Found {len(wanted_file_list)} CNS AR files")
    response = input('Create separate csv files for each?\nPress <Enter> for merged report. ')
    if re.match('^y',response.lower()):
        merge_output = False
    else:
        merge_output = True
        output_filename = 'CNS_PAYMENTS.csv'
        if os.path.isfile(output_filename):
            os.unlink('CNS_PAYMENTS.csv')
        out_file_handle = open('CNS_PAYMENTS.csv','a')
        out_file_handle.write(','.join(col_heading))
        out_file_handle.write("\n")

    for a_file in wanted_file_list:

        in_file_handle = open(a_file,'r')

        output_buffer = []
        AWM_record = []
        CCA_record = []

        for line in in_file_handle:
            line.strip()
            #print(line)
            #pattern = 

            # AAA RECORDS - FILE HEADERS  3 2 3 6 6 6 2 3 219
            if re.match('^AAA', line):
                #print("Found header>"+line)
                #record_id = line[0:3]
                cass_area_code = line[3:5]
                #airline_number = line[5:8]
                collection_date = '20' + line[8:10] + '-' + line[10:12] + '-' + line[12:14] #YYMMDD
                #payment_collection_date_end = line[14:20]
                disbursement_date = '20' + line[20:22] + '-' + line[22:24] + '-' + line[24:26] #YYMMDD
                #file_number = line[26:28]
                #currency = line[28:31]
                #reserved = line[31:250]

                #output_buffer.append("'"+",'".join([record_id,cass_area_code,airline_number,payment_collection_date_start,payment_collection_date_end,date_of_disbursement,file_number,date_of_billing,reserved]))
                #print(len(output_buffer))

                if False: #debugging output
                    #print(record_id)
                    print(cass_area_code)
                    #print(airline_number)
                    print(collection_date)
                    #print(payment_collection_date_end)
                    print(disbursement_date)
                    #print(file_number)
                    #print(currency)
                    #print(reserved)
                    input('<PAUSE>')

            # AWM RECORDS - 3 1 1 11 3 8 2 3 1 2 3 6 7 1 3 12 12 12 12 12 12 12 12 4 12 1 12 6 14 11 12 12 14 1
            elif re.match('^AWM', line):
                record_id = line[0:3]
                awb_serial_number = int(line[5:16]) #
                origin = line[18:21] #
                agent_code = '\'' + line[21:32] #
                awb_use_indicator = line[32:33]
                late_indicator = line[33:34]
                destination = line[36:39] #
                #awb_execution_date = '20' + line[39:41] + '-' + line[41:43] + '-' + line[43:45]
                weight = float(line[45:52])/10 #
                #weight_units = line[52:53]
                currency = line[53:56] #
                weight_charge_ppd = float(line[56:68])/100
                valuation_charge_ppd = float(line[68:80])/100
                charges_due_carrier_ppd = float(line[80:92])/100
                charges_due_agent_ppd = float(line[92:104])/100
                commission = float(line[156:168])/100
                adjustment_reason_code = line[169:171]
                adjustment_information = line[171:191]
                flight_date = '20' + line[193:195] + '-' + line[195:197] + '-' + line[197:199] #
                incentive = float(line[210:222])/100
                billing_period = int(line[245:249]) #
                incentive_parity = line[249:250]
                if incentive_parity == '-':
                    incentive *= -1

                net_due = round(weight_charge_ppd + charges_due_carrier_ppd + valuation_charge_ppd - commission - incentive, 2)
                #cass_area_code #
                #collection_date #
                #disbursement_date #

                AWM_record = [cass_area_code,collection_date,disbursement_date,flight_date,agent_code,awb_serial_number,
                                    origin,destination,weight,net_due,record_id,billing_period,currency,adjustment_reason_code,adjustment_information]
                if False: #debugging output
                    print_array(AWM_record)
                    print_array([weight_charge_ppd,charges_due_agent,charges_due_carrier_ppd,valuation_charge_ppd,commission,incentive])
                    input('<PAUSE>')

                output_buffer.append(AWM_record)


            #[CD]C[OR] RECORD - 3 1 1 3 8 2 3 11 6 3 11 6 1 12 1 12 1 12 1 12 1 12 12 12 12 12 1 1 7 3 67
            elif re.match('^[CDE]C[OR]', line):
                #print ("Found cca>"+line)
                record_id = line[0:3]
                #branch_office_code = line[3:4]
                #vat_indicator = line[4:5]
                awb_serial_number = int(line[5:16])
                #filler0 = line[16:18]
                origin = line[18:21]
                agent_code = '\'' + line[21:32]
                cca_number = '\'' + line[32:38]
                currency = line[38:41]
                #rate_of_exchange = line[41:52]
                awb_execution_date = '20' + line[52:54] + '-' + line[54:56] + '-' + line[56:58]
                #pp_cc_indicator1 = line[58:59]
                weight_charge = float(line[59:71])/100
                #pp_cc_indicator2 = line[71:72]
                valuation_charge = float(line[72:84])/100
                #pp_cc_indicator3 = line[84:85]
                #taxes = line[85:97]
                #pp_cc_indicator4 = line[97:98]
                charges_due_agent = float(line[98:110])/100
                #pp_cc_indicator5 = line[110:111]
                charges_due_carrier = float(line[111:123])/100
                #vat_on_awb_charges = line[123:135]
                commission = float(line[135:147])/100
                #vat_on_commission = line[147:159]
                incentive = float(line[159:171])/100
                incentive_indicator = line[171:172]
                if incentive_indicator == '-':
                    incentive *= -1
                #weight_indicator = line[172:173]
                weight = float(line[173:180])/10
                destination = line[180:183]
                adjustment_reason_code = line[183:185]
                adjustment_description = line[185:205]
                #reserved_space = line[205:245]
                billing_period = line[245:249]
                #filler1 = line[249:250]

                #cass_area_code #
                #collection_date #
                #disbursement_date #

                net_due = round(weight_charge + valuation_charge - charges_due_agent + charges_due_carrier - commission - incentive, 2)
                if re.search('O$', record_id):
                    net_due *= -1

                CCA_record = [cass_area_code,collection_date,disbursement_date,awb_execution_date,agent_code,awb_serial_number,
                                origin,destination,weight,net_due,record_id,billing_period,currency,adjustment_reason_code,adjustment_description,cca_number]

                if False: #debugging output
                    print_array(CCA_record)
                    print_array([record_id,weight_charge,valuation_charge,charges_due_agent,charges_due_carrier,commission,incentive])
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

        for line in output_buffer:
            for i in range(len(line)):
                if i > 0:
                    out_file_handle.write(','+str(line[i]))
                else:
                    out_file_handle.write(line[i])
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