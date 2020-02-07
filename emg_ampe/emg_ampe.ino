//2019.12.4
//emg計測
//emgControl3.pyと連動
//時間計測をPythonで行う
#define AIN1 A0
#define AIN2 A1
//#define AIN3 A2
//#define AIN4 A3

int ch1 = 0;
int ch2 = 0;
//int ch3 = 0;
//int ch4 = 0;
unsigned long time_m = 0;
unsigned long zero_time = 0;

void setup() {
  pinMode(AIN1, INPUT);
  pinMode(AIN2, INPUT);
  //pinMode(AIN3, INPUT);
  //pinMode(AIN4, INPUT);
  analogReference(INTERNAL);
  Serial.begin(115200);
}

void loop() {
  // put your main code here, to run repeatedly:
  int inputchar;
 
  /*inputchar = Serial.read();
  if(inputchar != -1){
    if(inputchar=='s'){
      zero_time = micros();
      while(1){ 
        /*
        if(micros() - zero_time > measure_time * 1000000){
          time_m = micros()-zero_time;
          break; 
        }  */ 
       /* inputchar = Serial.read();
        if(inputchar == 'o'){
          time_m = micros()-zero_time;
          break;
        }*/
        ch1 = analogRead(AIN1);
        ch2 = analogRead(AIN2);
        //ch3 = analogRead(AIN3);
        //ch4 = analogRead(AIN4);
        Serial.print(ch1);
        Serial.print(',');
        Serial.println(ch2);
        Serial.println("");
        //Serial.println(ch3);
        //Serial.println(ch4);
        delay(5);
        
      //}
      //time_m = micros()-zero_time;
      Serial.println(time_m);
    //}
  //}
}
