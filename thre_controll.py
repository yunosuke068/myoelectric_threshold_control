'''
2019.12.28
sudo python thre_hack.py
閾値による動作識別

'''

import serial   #モジュール名はpyserialだが, importする際はserialである
import scipy.io
import numpy as np
from pynput.keyboard import Key, Listener
import time
import random

import matplotlib as mpl
import matplotlib.pyplot as plt

ser = serial.Serial('/dev/tty.wchusbserial1410',115200,timeout=1)
ser_hack = serial.Serial('/dev/tty.usbmodem1421',115200,timeout=1)

#ポート番号の取得　ls -l /dev/tty.*
frame_shift = 0.01600000000000000000000000
frameshift_period = int(frame_shift*1000) #=16
frame_length = frameshift_period*4 # =64
ref = 1100/1024

sampling_rate = 1000    #サンプリングレート
cut_frequency = 5       #カットしたい周波数

#伝達関数の計算
sampling_cycle = 1/sampling_rate
cut_cycle = 1/cut_frequency
transfer = cut_cycle/(cut_cycle+sampling_cycle)


'''伝達関数'''
def transfer_function():
    sampling_cycle = 1/sampling_rate
    cut_cycle = 1/cut_frequency
    a = cut_cycle/(cut_cycle+sampling_cycle)
    return a

'''データ抽出（削除）'''
def extraction_delete(emg_stack):
    del_element = 0
    #削除する要素数
    del_element = len(emg_stack[0])-16
    for l in range(del_element):
        #削除する要素のインデックスをランダムに生成
        rand_num = random.randint(0, len(emg_stack[0])-1)
        #生成したインデックス値で要素を削除
        del emg_stack[0][rand_num]
        del emg_stack[1][rand_num]
    return emg_stack


'''データ抽出（追加）'''
def extraction_input(emg_stack):
    print('extraction_input')


'''IEMGへの変換'''
iemg1 = 0
iemg2 = 0
def convert_IEMG(emg_shortframe):
    global iemg1,iemg2
    #print('iemg1:{}, iemg2:{}'.format(iemg1, iemg2))
    iemg_stack1, iemg_stack2 = [], []
    for ii in range(len(emg_shortframe[0])):
        iemg1 = transfer*iemg1+(1-transfer)*emg_shortframe[0][ii]
        iemg2 = transfer*iemg2+(1-transfer)*emg_shortframe[1][ii]
        iemg_stack1.append(iemg1)
        iemg_stack2.append(iemg2)
    return [iemg_stack1, iemg_stack2]


'''CC特徴量抽出'''
def vectorCC(emg_frame):
    CCW = 5 #CC特徴量のデータ数
    N = len(emg_frame[0])
    hammingWindow = np.hamming(N)
    cc = []
    for ii in range(len(emg_frame)):
        if np.mean(emg_frame[ii]) == 0:
            cps = np.zeros(CCW)
        else:
            cps = np.real(np.fft.ifft(20*np.log10(np.abs(np.fft.fft(emg_frame[ii]*hammingWindow, N)))))
            #データ抽出
            cps = cps[0:CCW]
        cc.extend(cps)
    return cc


'''動作指示'''
#動作区間
def motion_func(now_time, sec_product):
    section1, section2, section3, section4, section5 = 1.000,2.000,3.000,4.000,5.000
    count = sec_product
    motion = 0
    if ((section1+count*4.000 <= now_time)and(section2+count*4.000 > now_time))or((section3+count*4.000 <= now_time)and(section4+count*4.000 > now_time)):
        motion = 0

    elif (section2+count*4.000 <= now_time)and(section3+count*4.000 > now_time):
        motion = 1

    elif (section4+count*4.000 <= now_time)and(section5+count*4.000 > now_time):
        motion = 2

    else:
        motion = 0
    #print('{}, {:.4f}, {}, {}, {}, {}, {}'.format(motion, now_time, section1+count*4.000, section2+count*4.000, section3+count*4.000, section4+count*4.000, section5+count*4.000))
    return motion


'''グラフ描画'''
def graph_plot(emg):
    y = emg[0]
    x = np.arange(len(y))
    plt.plot(x, y)
    plt.savefig("matplotlib_example_single.png")

def calibration():
    #計測時間
    measure_time = 8
    #計測用Arduinoへの計測開始指示
    ser.write(bytes('s','utf-8'))
    #データ抽出タイミング
    frame_shift_sum = frame_shift
    #計測データの保管用
    emg_stack1, emg_stack2 = [], []
    #動作指示保存用
    motion_vector  =[]
    motion = 0
    sec_product = 0
    #1フレームのデータ保管用
    emg_frame     = np.empty((2,0), float)
    iemg_frame    = np.empty((2,0), float)
    vector_frame  = np.empty((0,2), float)
    vector = np.empty((0,12), float)
    #emg,iemgデータ保存用
    emg = np.empty((2,0), float)
    iemg = np.empty((2,0), float)
    zero_time = time.time()
    while True:
        now_time = time.time() - zero_time
        #Arduinoのデータ読み取り
        data = ser.readline().split()
        if not now_time > 1.000000000000000000:
            print('{:.4f}, {}'.format(now_time, data))
        #nullデータでないか判別. もしnullならbreak
        else:
            if not len(data) == 0:
                #電圧値mVに変換
                emg1 = float(data[0])*ref
                emg2 = float(data[1])*ref
                emg_stack1.append(emg1)
                emg_stack2.append(emg2)
                #0.016s毎にデータ抽出
                if now_time > frame_shift_sum+1:
                    emg_stack = [emg_stack1, emg_stack2]
                    #データ抽出(削除)
                    if len(emg_stack[0])>frameshift_period:
                        emg_shortframe = extraction_delete(emg_stack)
                    #データ抽出(追加)
                    elif len(emg_stack[0])<frameshift_period:
                        extraction_input(emg_stack)
                    #IEMGへの変換
                    iemg_shortframe = convert_IEMG(emg_shortframe) #16データ
                    #emgデータの保存
                    emg = np.hstack([emg,emg_shortframe])
                    iemg = np.hstack([iemg,iemg_shortframe])
                    #64データまでためる
                    emg_frame = np.hstack([emg_frame, emg_shortframe])
                    iemg_frame = np.hstack([iemg_frame, iemg_shortframe])
                    #データ抽出タイミングの更新
                    frame_shift_sum = frame_shift_sum + frame_shift
                    #emg_stack1, emg_stack2の初期化
                    emg_stack1, emg_stack2 = [], []


                    #動作指示
                    if now_time >= 6.000+4.000*sec_product:
                        sec_product += 1
                    motion = motion_func(now_time, sec_product)
                    motion_vector.append(motion)

                    print('{}, {:.4f}, vector len: {}, motion len: {}, emg len: {}, iemg len: {}'.format(motion, now_time, len(vector), len(motion_vector), len(emg[0]), len(iemg[0])))
                elif now_time > measure_time+1:
                    #print('finish')
                    ser.write(bytes('o','utf-8'))

            else:
                break

    print('calibration finish!')
    #motion_vectorの整形
    motion_vector = np.delete(motion_vector,[0,2,1])
    print('vector length : {}, motion length : {}'.format(len(vector), len(motion_vector)))
    print('emg length : {}, iemg length : {}'.format(len(emg[0]), len(iemg[0])))
    #計測データのプロット
    graph_plot(emg)
    threshold = calib_threshold(iemg)
    dumy = input('please press enter')
    yn = input('Do you want to save the data? (y/n) : ')
    if yn == 'y':
        #学習データの保存
        #filename = input('input filename :')
        #scipy.io.savemat('train_data'+str(filename)+'.mat', {'train_data'+str(filename):train_data})
        print('save data.')
        print('To continue measurement, please press "c" key.')
        print('To finish measurement, please press "esc" key.')
        control(threshold)
    else:
        print('Did not save.')
        print('To continue measurement, please press "c" key.')
        print('To finish measurement, please press "esc" key.')

def calib_threshold(data):
    dataMax = data.max(axis=1)
    print(dataMax)
    threshold = dataMax*5/10
    fig = plt.figure()
    length = np.arange(len(data[0]))
    ax1 = fig.add_subplot(2,1,1)
    ax2 = fig.add_subplot(2,1,2)
    ax1.plot(length, data[0], linewidth=0.5)
    ax1.plot(length, np.full(len(data[0]), threshold[0]), linewidth=0.5)
    ax2.plot(length, data[1], linewidth=0.5)
    ax2.plot(length, np.full(len(data[0]), threshold[1]), linewidth=0.5)
    fig.savefig("IEMGthreshold.png")
    return threshold

def control(threshold):
    #計測時間
    measure_time = 60
    #計測用Arduinoへの計測開始指示
    ser.write(bytes('s','utf-8'))
    #データ抽出タイミング
    frame_shift_sum = frame_shift
    #計測データの保管用
    emg_stack1, emg_stack2 = [], []
    #動作指示保存用
    motion = 0
    sec_product = 0
    #1フレームのデータ保管用
    emg_frame     = np.empty((2,0), float)
    iemg_frame    = np.empty((2,0), float)
    vector_frame  = np.empty((0,2), float)
    vector = np.empty((0,12), float)
    #emg,iemgデータ保存用
    emg = np.empty((2,0), float)
    iemg = np.empty((2,0), float)
    zero_time = time.time()
    while True:
        now_time = time.time() - zero_time
        #Arduinoのデータ読み取り
        data = ser.readline().split()
        if not now_time > 1.000000000000000000:
            print('{:.4f}, {}'.format(now_time, data))
        #nullデータでないか判別. もしnullならbreak
        else:
            if not len(data) == 0:
                #電圧値mVに変換
                emg1 = float(data[0])*ref
                emg2 = float(data[1])*ref
                emg_stack1.append(emg1)
                emg_stack2.append(emg2)
                #0.016s毎にデータ抽出
                if now_time > frame_shift_sum+1:
                    emg_stack = [emg_stack1, emg_stack2]
                    #データ抽出(削除)
                    if len(emg_stack[0])>frameshift_period:
                        emg_shortframe = extraction_delete(emg_stack)
                    #データ抽出(追加)
                    elif len(emg_stack[0])<frameshift_period:
                        extraction_input(emg_stack)
                    #IEMGへの変換
                    iemg_shortframe = convert_IEMG(emg_shortframe) #16データ
                    iemg_mean = np.array(iemg_shortframe).mean(axis=1)

                    motion = idenfication(iemg_mean, threshold)

                    #hackberry control
                    if motion == 0:
                        print('{}, neutral, {:.4f}, threshold1:{:.4f}, {:.4f}, threshold2:{:.4f}, {:.4f}'.format(motion, now_time, threshold[0], iemg_mean[0], threshold[1], iemg_mean[1]))
                    elif motion == 1:
                        ser_hack.write(bytes('g', 'utf-8'))
                        print('{}, grasp, {:.4f}, threshold1:{:.4f}, {:.4f}, threshold2:{:.4f}, {:.4f}'.format(motion, now_time, threshold[0], iemg_mean[0], threshold[1], iemg_mean[1]))
                    elif motion == 2:
                        ser_hack.write(bytes('d', 'utf-8'))
                        print('{}, divide, {:.4f}, threshold1:{:.4f}, {:.4f}, threshold2:{:.4f}, {:.4f}'.format(motion, now_time, threshold[0], iemg_mean[0], threshold[1], iemg_mean[1]))

                    #emgデータの保存
                    emg = np.hstack([emg,emg_shortframe])
                    iemg = np.hstack([iemg,iemg_shortframe])
                    #データ抽出タイミングの更新
                    frame_shift_sum = frame_shift_sum + frame_shift
                    #emg_stack1, emg_stack2の初期化
                    emg_stack1, emg_stack2 = [], []


                    #print('{}, {:.4f}, threshold1:{:.4f}, {:.4f}, threshold2:{:.4f}, {:.4f}'.format(motion, now_time, threshold[0], iemg_mean[0], threshold[1], iemg_mean[1]))
                elif now_time > measure_time+1:
                    #print('finish')
                    ser.write(bytes('o','utf-8'))

            else:
                break

    print('finish!')
    dumy = input('please press enter')
    yn = input('Do you want to save the data? (y/n) : ')
    if yn == 'y':
        print('save data.')
        print('To continue measurement, please press "c" key.')
        print('To finish measurement, please press "esc" key.')
    else:
        print('Did not save.')
        print('To continue measurement, please press "c" key.')
        print('To finish measurement, please press "esc" key.')

def idenfication(data, threshold):
    data1 = data[0]
    data2 = data[1]
    if (data1 < threshold[0])&(data2 < threshold[1]):
        motion = 0
    elif (data1 > threshold[0])&(data2 < threshold[1]):
        motion = 1
    elif (data1 < threshold[0])&(data2 > threshold[1]):
        motion = 2
    elif (data1 > threshold[0])&(data2 > threshold[1]):
        motion = 1
    return motion

    if ave_iemg1 >= threshold:
        ser_hack.write(bytes('g', 'utf-8'))
        print('{}, grasp, {:.4f},  threshold : {}, ave_iemg : {}, {}'.format(moti, now_time, threshold, ave_iemg, frame_num))
        gd_count[0] = 1
    elif ave_iemg1 < threshold:
        ser_hack.write(bytes('d', 'utf-8'))
        print('{}, divide, {:.4f},  threshold : {}, ave_iemg : {}, {}'.format(moti, now_time, threshold, ave_iemg, frame_num))
        gd_count[0] = 0


def on_press(key):
    if str(key) == "'c'":
        print('calibration!!!')
        print('Ready....')
        for i in range(3, 0, -1):
            print(i);
            time.sleep(1)
        calibration()

    if str(key) == "'g'":
        ser.write(bytes(key.char,'utf-8'))
        print('\n')

    if str(key) == "'d'":
        ser.write(bytes(key.char,'utf-8'))
        print('\n')

    elif str(key) == "'s'":
        print('key {0} pressed. Please push enter...'.format(key))
        dumy_input = input()
        print('How long do you measure?')
        measure_time = float(input()) + frame_shift
        print('Ready....')
        for i in range(3, 0, -1):
            print(i);
            time.sleep(1)
        print('計測スタート')
        ser.write(bytes(key.char,'utf-8'))
        #serial_read1() #入力4
        serial_read_input_2(measure_time) #入力2


def on_release(key):
    #print('{0} released'.format(key))
    if key == Key.esc:
        # Stop listener
        print('close program')
        return False


def main():
    print('connecting...')
    time.sleep(3)
    print('connecting finish!')
    with Listener(
        on_press = on_press,    #on_press, on_realeaseはpynputによるもの
        on_release= on_release  #press>on_press関数> on_press or on_release
    ) as listener:
        listener.join()
    ser.close()

if __name__ == "__main__":
    main()
