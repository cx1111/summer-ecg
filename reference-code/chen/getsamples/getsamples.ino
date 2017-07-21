#include <compat/deprecated.h>
//http://www.arduino.cc/playground/Main/FlexiTimer2
#include <FlexiTimer2.h>

#define SAMPFREQ 200                // Samplig frequency (in Hz)
#define TIMER2VAL (1000/(SAMPFREQ)) // Sampling period (in msecs)
#define BAUDRATE 115200             // Baudrate on the serial line
#define BUFLEN 80                   // Record length

// --------- Global Variables
volatile unsigned long int Basetime;

int Data;        // Data buffer (two positions)
volatile boolean full[]={false,false};   // Data buffer state
volatile unsigned char b=0;              // Ready buffer index

/*
 * Sampling function
 * Check data buffer cell is free
 * Fill buffer with data from Olimex-EKG board
 * Rotate the buffer
 */
void Timer2_Overflow_ISR() {  
  int i;
  unsigned long int t;
  
  if ( full[b] ) {
      Serial.println("fail");
      return;
  }  
 
  Data = analogRead(0);
  
  full[b]=true;
  b=b^1; //toggle 0,1 values
}

/*
 * Initializes the serial line (see constant for the Baudrate)
 * Sets the basetime for the timestamps
 * Initializes the interrupt that controls sampling
 */
void setup() {
  Serial.begin(BAUDRATE);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for Leonardo only
  }
  Basetime=millis();
  noInterrupts();
  FlexiTimer2::set(TIMER2VAL, Timer2_Overflow_ISR);
  FlexiTimer2::start();
  interrupts();
}


/*
 * Check if data available
 * If there there is no data available in the data buffer, 
 * proceed with another loop
 * When data is available:
 * - compute the timestamp and format as hh:mm:ss.mmm in the
 *   record string
 * - add the 6 raw data from Olimex-ECG board to the on the record 
 *   string
 * - send the record on the serial line
 * - mark the current data buffer as empty
 * - proceed with another loop
 */
void loop() {
  int i=0;
  char Next=b^1;
  unsigned long int t;
  
  if ( full[Next] ) {
    
    Serial.println(Data, DEC);
    
    full[Next]=false;
  }
}

