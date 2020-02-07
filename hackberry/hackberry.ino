/*
 * 2019.12.15
 * Hackberry 筋電操作
 * 動作テスト 
 * ver.1
 */
#include <Servo.h> //サーボライブラリ

#define pinServoIndex 3
#define pinServoOther 5
#define pinServoThumb 6

//Hardware モーター
Servo servoIndex; //index finger Servoオブジェクト"servoIndex"の作成
Servo servoOther; //other three fingers
Servo servoThumb; //thumb

const int outThumbMax = 140;//right:open, left:close (140)親指サーボ
const int outIndexMax = 130;//right:open, left:close (130)人差
const int outOtherMax = 145;//right:open, left:close ３指
const int outThumbMin = 47;//right:close, left:open (47)
const int outIndexMin = 15;//right:close, left:open (27)
const int outOtherMin = 75;//right:close, left:open(105)

int outThumbOpen,outThumbClose,outIndexOpen,outIndexClose,outOtherOpen,outOtherClose;


void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);

  outThumbOpen=outThumbMin; outThumbClose=outThumbMax;
  outIndexOpen=outIndexMin; outIndexClose=outIndexMax;
  outOtherOpen=outOtherMin; outOtherClose=outOtherMax;
  
  servoIndex.attach(pinServoIndex);
  servoOther.attach(pinServoOther);
  servoThumb.attach(pinServoThumb);

  servoIndex.write(outIndexOpen);//サーボの角度を入力 outIndexOpenがサーボに与える角度
  servoOther.write(outOtherOpen);//
  servoThumb.write(outThumbOpen);//outIndexOpen=outIndexMax、初期位置と最大角

}

void loop() {
  // put your main code here, to run repeatedly:
  servoIndex.write(outIndexOpen);
  servoOther.write(outOtherOpen);
  //servoThumb.write(outThumbOpen);
  delay(1000);
  servoIndex.write(outIndexClose);
  servoOther.write(outOtherClose);
  //servoThumb.write(outThumbClose);
  delay(1000);

}
