import { Component, ViewChild, ChangeDetectorRef, OnInit, ElementRef, OnDestroy} from '@angular/core';
import { Platform, IonContent } from '@ionic/angular';
import axios from 'axios';
import { VoiceRecorder, GenericResponse, RecordingData, CurrentRecordingStatus } from 'capacitor-voice-recorder';
import { Device } from '@capacitor/device';
import { HttpClient } from '@angular/common/http';
import { SpeechRecognition } from '@capacitor-community/speech-recognition';
import { Subscription } from 'rxjs';

import { PorcupineService } from '@picovoice/porcupine-angular';
import { BuiltInKeyword, PorcupineKeyword } from '@picovoice/porcupine-web';
import { CobraWorker } from "@picovoice/cobra-web";
import { WebVoiceProcessor } from "@picovoice/web-voice-processor";

interface Message {
  speaker: 'User' | 'Bot';
  text: string;
}

interface PresetConversation {
  title: string;
  id: string;
  messages: Message[];
}

const delay = (ms: number) => new Promise(res => setTimeout(res, ms));

const base_api_url = ""

@Component({
  selector: 'app-tab1',
  templateUrl: 'tab1.page.html',
  styleUrls: ['tab1.page.scss']
})
export class Tab1Page {
  @ViewChild('chatContainer', { static: false }) chatContainer!: ElementRef;

  conversation: { speaker: string, text: string }[] = [];
  contextConv: { speaker: string, text: string }[] = [];
  openAiApiKey: string = '';  // no longer needed all openai api calls are server side
  writtenText: string = '';
  deviceType!: string;
  isRecording: boolean = false;
  wakeWords: string[] = ['hello pay activ', 'hey pay activ', 'hello payactiv', 'hey payactiv', 'hey pactiv', 'hello pactiv']; // Set your wake word here
  basePresetConversations: PresetConversation[] = [
    { title: 'What is Payactiv', id: 'payactiv', messages: [{ speaker: 'User', text: 'What is Payactiv?' }, { speaker: 'Bot', text: 'Payactiv is a digital wallet that allows users over 18 to pay bills, set money aside automatically, and gain insights into their spending, while also offering Earned Wage Access as a benefit through partnerships with companies.'}] },
    { title: 'What is EWA', id: 'ewa', messages: [{ speaker: 'User', text: 'What is Earned Wage Access?' }, { speaker: 'Bot', text: 'Earned Wage Access (EWA) is a benefit that allows employees to access a portion of their earned wages before the scheduled payday, provided their employer partners with an EWA provider.'}] },
    { title: 'Account  Balance', id: 'balance', messages: [{speaker: 'User', text: "What is my Account Balance?" }, { speaker: 'Bot', text: 'Please enter the account that you would like to know the balance of' }] },
    { title: 'Transfer Money', id: 'transfer', messages: [ {speaker: 'User', text: "Transfer Money" }, { speaker: 'Bot', text: 'Which account woud you like to transfer from' }] },
  ];
  presetConversations: PresetConversation[] = this.basePresetConversations
  accountPresetConversations: PresetConversation[] = []
  amountPreset : PresetConversation[] = []
  confirmPreset : PresetConversation[] = [
    { title: 'Yes', id: 'yes', messages: [{speaker: 'User', text: "Yes" }] },
    { title: 'No', id: 'no', messages: [ {speaker: 'User', text: "No" }] },
  ]
  listening: boolean = false;
  currTranscription: string = ""
  wakeWord: string = "Hello" // temporary wake word for development

  private keywordSubscription: Subscription;
  private isLoadedSubscription: Subscription;
  private isListeningSubscription: Subscription;
  private errorSubscription: Subscription;

  isLoaded = false;
  isListening = false;
  error: Error | string | null = null;

  detections: Array<string> = [];
  cobra!: CobraWorker;
  accounts : any[] = []

  constructor(private platform: Platform, private cdr: ChangeDetectorRef, private http: HttpClient, private porcupineService: PorcupineService) {
    // Subscribe to Porcupine Keyword detections
    // Store each detection, so we can display it in an HTML list
    this.keywordSubscription = porcupineService.keywordDetection$.subscribe(
      porcupineSubscription => {
        this.detections = [...this.detections, porcupineSubscription.label];
        this.playSpeechSound()
        this.toggleListening()
      });

    // Subscribe to isListening, isLoaded, and error
    this.isLoadedSubscription = porcupineService.isLoaded$.subscribe(
      isLoaded => {
        this.isLoaded = isLoaded;
      });
    this.isListeningSubscription = porcupineService.isListening$.subscribe(
      isListening => {
        console.log('Porcupine isListening status:', isListening);
        this.isListening = isListening;
      });
    this.errorSubscription = porcupineService.error$.subscribe(
      error => {
        this.error = error;
      });
    this.platform.ready().then(() => {
      this.checkDeviceCapability();
    });
  }

  public async stop(): Promise<void> {
    await this.porcupineService.stop();
  }

  public async start(): Promise<void> {
    await this.porcupineService.start();
  }

  public async initEngine(): Promise<void> {
    const accessKey = "";
    const keyword = 'Hey-pay-active_en_wasm_v3_0_0.ppn';
    const keywordPath = './assets/' + keyword;
    const contextPath = './assets/porcupine_params.pv';

    const keywordModel = {
      publicPath: keywordPath,
      label: "payactiv"
    }

    const porcupineModel = {
      publicPath: contextPath
    }

    if (this.porcupineService.isLoaded$) {
      await this.porcupineService.release();
    }

    if (accessKey.length >= 0) {
      try {
        await this.porcupineService.init(
          accessKey,
          keywordModel,
          porcupineModel
        );
      }
      catch (error: any) {
        console.log(error)
        this.error = error;
      }
    }
    this.cobra = await CobraWorker.create(
        accessKey,
        this.voiceProbabilityCallback.bind(this)
    );
    // Initialize WebVoiceProcessor
    WebVoiceProcessor.setOptions({
        outputSampleRate: 16000,  // Target sample rate of recorded audio
        frameLength: 512,   // Number of samples per frame (1 second of audio)
        filterOrder: 50,                     // Keep default filter order
        deviceId: null                       // Use default microphone
    }, true)
    // await WebVoiceProcessor.subscribe(cobra)

    // setInterval(async () => {
    //   const blob = await WebVoiceProcessor.audioDump(500)
    //   const pcm = await this.convertBlobToInt16Array(blob)
    //   this.cobra.process(pcm)
    // }, 500)
  }

  voiceProbabilityCallback(voiceProbability: number) {
    if (voiceProbability < 0.015) {
      console.log("No more voice stopping recording...", voiceProbability)
      this.stopRecordingWeb()
    }
    console.log("Voice probability is ", voiceProbability)
  }


  public async release(): Promise<void> {
    await this.porcupineService.release();
  }

  async getAudioAsInt16Array(durationMs: number): Promise<Int16Array> {
    try {
        // Step 1: Get the Blob from audioDump
        const audioBlob = await WebVoiceProcessor.audioDump(durationMs);

        // Step 2: Convert the Blob to an ArrayBuffer
        const arrayBuffer = await audioBlob.arrayBuffer();

        // Step 3: Convert the ArrayBuffer to an Int16Array
        const int16Array = new Int16Array(arrayBuffer);

        // Return the Int16Array
        return int16Array;
    } catch (error) {
        console.error('Error converting Blob to Int16Array:', error);
        throw error;
    }
  }

  async ngOnInit() {
    const info = await Device.getInfo();
    this.deviceType = info.platform;
    console.log('Device Type:', this.deviceType)
    const canRecord = await VoiceRecorder.canDeviceVoiceRecord()
    if (canRecord.value == true) {
      const res = await this.checkPermissions();
      if (res.value != true) {
        await this.requestPermissions();
      }
    }
    // For wake word functionality
    // this.startContinuousListening(); 
    this.checkAndRequestPermissions()
    await this.loadAmtPresets()
    await this.initEngine()
    await this.start()

  }

  async checkAndRequestPermissions() {
    const permissionStatus = await SpeechRecognition.checkPermissions();

    if (permissionStatus.speechRecognition !== 'granted') {
      await SpeechRecognition.requestPermissions();
    }
  }

  ngOnDestroy(): void {
    this.keywordSubscription.unsubscribe();
    this.isLoadedSubscription.unsubscribe();
    this.isListeningSubscription.unsubscribe();
    this.errorSubscription.unsubscribe();
    this.porcupineService.release();
  }

  async saveConversation() {
    try {
      console.log('Sending conversation:', JSON.stringify(this.conversation)); // Debugging line
      const response = await axios.post(base_api_url + 'api/save-data', this.conversation);      
      console.log('Data saved successfully:', response.data);
    } catch (error) {
      console.error('Error saving data:', error);
    }
  }

  async loadAmtPresets() {
    for (let i = 0; i < 10; i++) {
      const amt = 50 * (i + 1)
      this.amountPreset.push({
        "title": `$${amt}`,
        "id": "amount",
        "messages": [{"speaker": 'User', "text":  `$${amt}`}]
      })
    }
  }

  async loadPresetConversation(preset: PresetConversation) {
    const id = preset.id;
    console.log("Called preset with id ", id)
    if (id == "payactiv" || id == "ewa") {
      this.conversation = preset.messages.slice();
      this.contextConv = preset.messages.slice();
      this.scrollToBottom();
    } else {
      if (id == "balance") {
        await this.fetchAcctInfo();
        this.presetConversations = this.accountPresetConversations
        this.conversation = preset.messages.slice();
        this.contextConv = preset.messages.slice();
        this.scrollToBottom()
      } else if (id == "transfer") {
        await this.fetchAcctInfo();
        this.presetConversations = this.accountPresetConversations
        this.conversation = preset.messages.slice(); 
        this.contextConv = preset.messages.slice();
        this.scrollToBottom()
      } else {
        this.conversation = this.conversation.concat(preset.messages);
        this.contextConv = this.contextConv.concat(preset.messages);
        this.respondToQuestion(preset.messages[0]["text"], false)
      }
    }
    this.scrollToBottom();
  }

  async startContinuousListening() {
    console.log("Listening function called")
    if (this.listening) {
      return; // Prevent multiple simultaneous listening sessions
    }
    SpeechRecognition.removeAllListeners()
    this.listening = true;

    try {
      // Start speech recognition with partial results
      await SpeechRecognition.start({
        language: 'en-US',
        maxResults: 1,
        partialResults: true, // Enable partial results
      });

      // Listen to partial results
      SpeechRecognition.addListener('partialResults', (data: { matches: string[] }) => {
        if (data.matches && data.matches.some((match: string) => match.toLowerCase().includes(this.wakeWord.toLowerCase()))) {
          console.log('Wake word detected:', data.matches);
          this.stopListening(); // Stop listening when wake word is detected
        }
      });

      // Listen to listening state to restart listening if it stops unintentionally
      SpeechRecognition.addListener('listeningState', (state: { status: 'started' | 'stopped' }) => {
        if (state.status === 'stopped' && this.listening) {
          console.log('Listening stopped unexpectedly, restarting...');
          this.listening = false;
          this.startContinuousListening();
        }
      });

    } catch (error) {
      console.error('Error during speech recognition:', error);
      // Restart listening after an error
      setTimeout(() => this.startContinuousListening(), 1000);
    }
  }

  async stopListening() {
    this.listening = false;

    try {
      await SpeechRecognition.stop();
      console.log('Speech recognition stopped.');
      // Remove listeners to prevent multiple triggers
      await SpeechRecognition.removeAllListeners();
      this.toggleListening();
    } catch (error) {
      console.error('Error stopping speech recognition:', error);
    }
  }

  handleSpeechResult(results: string[]) {
    for (const result of results) {
      if (this.wakeWords.some(word => result.toLowerCase().includes(word))) {
        this.onWakeWordDetected(result);
        break;
      }
    }
  }

  onWakeWordDetected(detectedWord: string) {
    console.log(`Wake word detected: ${detectedWord}`);
    // stop listening for wake word
    this.stopListening();
    // start recording
    this.toggleListening()
  }

  async checkDeviceCapability() {
    const result: GenericResponse = await VoiceRecorder.canDeviceVoiceRecord();
    console.log('Can device voice record:', result.value);
  }

  async toggleListening() {
    this.cdr.detectChanges();
    const func_dict: { [key: string]: () => Promise<void> }= {
      "startRecordingMobile": this.startRecordingMobile.bind(this),
      "stopRecordingMobile": this.stopRecordingMobile.bind(this),
      "startRecordingWeb": this.startRecordingWeb.bind(this),
      "stopRecordingWeb": this.stopRecordingWeb.bind(this)
    }
    let str: string = '';

    if (!this.isRecording) {
      str += "startRecording"
    } else {
      str += "stopRecording"
    }
    if (this.deviceType == "ios" || this.deviceType == "android") {
      str += "Mobile"
    } else {
      str += "Web"
    }
    console.log(str)
    await func_dict[str]()
  }

  async checkPermissions() {
    try {
      const checkPermissionsResult = await VoiceRecorder.hasAudioRecordingPermission();
      console.log('checkPermissionsResult: ' + JSON.stringify(checkPermissionsResult));
      return checkPermissionsResult;
    } catch (error) {
      console.error('checkPermissions Error: ' + JSON.stringify(error));
      return {"value": false}
    }
  }

  async requestPermissions() {
    try {
      const requestPermissionsResult = await VoiceRecorder.requestAudioRecordingPermission();
      console.log('requestPermissionsResult: ' + JSON.stringify(requestPermissionsResult));
    } catch (error) {
      console.error('requestPermissions Error: ' + JSON.stringify(error));
    }
  }

  async playSpeechSound() {
    const audio = new Audio('./assets/sfx/speech.mp3');
    await audio.play();
  }
  
  async startRecordingMobile() {
    console.log("Mobile Recording function called")
    if (this.listening) {
      return; // Prevent multiple simultaneous listening sessions
    }
    SpeechRecognition.removeAllListeners()
    this.listening = true;
    this.isRecording = true;
  
    try {
      // Start speech recognition with partial results
      await SpeechRecognition.start({
        language: 'en-US',
        maxResults: 1,
        partialResults: true, // Enable partial results
      });
      await VoiceRecorder.startRecording();
  
      // Listen to partial results
      SpeechRecognition.addListener('partialResults', (data: { matches: string[] }) => {
        if (data.matches) {
          this.currTranscription = data.matches.join(" ")
        }
      });
  
      // Listen to listening state to restart listening if it stops unintentionally
      SpeechRecognition.addListener('listeningState', (state: { status: 'started' | 'stopped' }) => {
        if (state.status === 'stopped' && this.listening) {
          this.stopRecordingMobile()
        }
      });
  
      let tempTranscript = this.currTranscription
      await delay(2000)
      while (true) {
        await delay(2000);
        if (tempTranscript === this.currTranscription) {
          this.stopRecordingMobile();
          break;
        }
        tempTranscript = this.currTranscription;
      }
  
    } catch (error) {
      console.error('Error during speech recognition:', error);
      return
    }
  }
  
  async stopRecordingMobile() {
    this.listening = false;
    this.isRecording = false;
    try {
        // Stop speech recognition
        await SpeechRecognition.stop();
        console.log('Recording stopped with speech recognition');
        SpeechRecognition.removeAllListeners();
        const result: RecordingData = await VoiceRecorder.stopRecording();
        this.isRecording = false;
        const blob = this.base64ToBlob(result.value.recordDataBase64, result.value.mimeType);
        this.transcribeAudio(blob)
        this.cdr.detectChanges();
    } catch (error) {
        console.error('stopRecordingMobile Error:', error);
    }
  }

  async startRecordingWeb() {
    try {
      // this.stopListening();
      
      this.stop()
      const permissionResult: GenericResponse = await VoiceRecorder.requestAudioRecordingPermission();
      if (permissionResult.value) {
        await VoiceRecorder.startRecording();
        this.isRecording = true;
        this.cdr.detectChanges();
        await delay(2000)
        // if (this.isRecording) {
        //   await WebVoiceProcessor.subscribe(this.cobra)
        // }

        while (this.isRecording) {
          const pcm = await this.getAudioAsInt16Array(1000)
          this.cobra.process(pcm)
        }
      } else {
        throw new Error("Recording permission denied")
      }
    } catch (error) {
      console.error('Start recording error:', error);
    }
  }

  async stopRecordingWeb() {
    try {
      // await WebVoiceProcessor.unsubscribe(this.cobra)
      const result: RecordingData = await VoiceRecorder.stopRecording();
      this.isRecording = false;
      this.cdr.detectChanges();
      console.log("MS Recording duration is", result.value.msDuration)
      const blob = this.base64ToBlob(result.value.recordDataBase64, result.value.mimeType);
      this.transcribeAudio(blob);
      // this.startListening();
    } catch (error) {
      console.error('Stop recording error:', error);
    }
  }

  base64ToBlob(base64: string, mime: string): Blob {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mime });
  }

  async transcribeAudio(blob: Blob) {
    const formData = new FormData();
    formData.append('file', blob, 'audio.m4a');
    formData.append('model', 'whisper-1');

    try {
      // const response = await fetch('https://api.openai.com/v1/audio/transcriptions', {
      //   method: 'POST',
      //   headers: {
      //     'Authorization': `Bearer ${this.openAiApiKey}`,
      //   },
      //   body: formData,
      // });

      const response = await axios.post(base_api_url + '/api/transcribe', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      const data = await response.data;
      console.log('Transcription:', data.text);
      console.log("Data", data)
      if (data.error) {
        this.conversation.push({ speaker: 'Bot', text: "Error transcribing text, please try again..." })
        return
      }
      this.conversation.push({ speaker: 'User', text: data.text })
      this.contextConv.push({ speaker: 'User', text: data.text })
      this.respondToQuestion(data.text, true);
    } catch (error) {
      console.error('Transcription error:', error);
    }
  }
  
  async sendMessage() {
    const str = this.writtenText;
    if (str == "") {
      return;
    }
    this.writtenText = '';
    this.conversation.push({ speaker: 'User', text: str });
    this.contextConv.push({ speaker: 'User', text: str });
    this.respondToQuestion(str, false);  
  }

  async fetchAcctInfo() {
    try {
      // const response = await axios.get('https://cax30kkgd9.execute-api.us-east-1.amazonaws.com/v1/accounts'); 
      const response = await axios.get('/api/accounts')     
      const assets = response.data.assets; // response.data.data.assets
      this.accounts = [];
      let output = ""
      this.accountPresetConversations = []
      const ewa_info = await this.fetch_ewa_details()
      let info = "Accessible Earnings Info: "
      if (ewa_info["message"] == "Success") {
        info += "Accessible Earnings Amount: $" + ewa_info["data"]["accessibleEarningsAmount"] + ", Account Max: $" + ewa_info["data"]["maxAccessibleAmount"] + ", Total Earnings $" + ewa_info["data"]["totalEarningsAmount"] + ", Percent of Earnings Accessible: " + ewa_info["data"]["allowedPercentage"] + ", Earning Rate: $" + ewa_info["data"]["incomeRate"] + ", hours received at: " + ewa_info["data"]["hoursLastReceivedAt"] + ", hours worked: " + ewa_info["data"]["totalHoursReceived"] + "\n" 
      } else {
        info += ewa_info["message"]
      }
      info += " If a user reports incorrect accessible earnings notify them of the last time EWA balance was updated and ask them to check again in a couple hours"
      for (let asset of assets) {
        this.accounts.push({
          "id": asset.id,
          "name": asset.title === "Accessible Earnings" ? asset.title + " (EWA Account)" : asset.title.includes("Payactiv Card") ? asset.title + " (PA Card)" : asset.title,
          "balance": asset.amount
        })
        output += `Account Name: ${asset.title === "Accessible Earnings" ? asset.title + " (EWA Account) " + info  : asset.title.includes("Payactiv Card") ? asset.title + " (PA Card)" : asset.title}, Account ID: ${asset.id}, Account Balance: ${asset.amount}\n`
        this.accountPresetConversations.push({
          "title": asset.title,
          "id": asset.id,
          "messages": [{speaker: 'User', text: `${asset.title}` },]
        })
      }
      return output
    } catch (error) {
      console.error('Error fetching account data', error)
      return {"User Accounts": "Could not fetch user account information"}; 
    }
  }

  async intentClassification(text: string): Promise<any> {
    try {
      let apiUrl = base_api_url + '/api/fetch_intent';
      const data = {
        query: text
      }
      const response = await axios.post(apiUrl, data);
      console.log(response)
      return response.data;
    } catch (error) {
      console.error('Error:', error);
      return "error";
    }
  }

  async semanticSearch(text: string): Promise<any> {
    try {
      let apiUrl = base_api_url + '/api/semantic_search';
      const data = {
        query: text
      }
      const response = await axios.post(apiUrl, data);
      console.log(response)
      return response.data;
    } catch (error) {
      console.error('Error:', error);
      throw error;
    }
  }

  async fetchContext(question: string, fetched_intent: string) {
    let intent = null
    for (let i = 0; i < this.accountPresetConversations.length; i++) {
      if (question == this.accountPresetConversations[i].title) {
        intent = 'balance'
      }
    }
    if (intent == null) {
      intent = fetched_intent
    }
    let messages = [{ 
      role: 'system', 
      content: `You are a helpful Payactiv application voice and text assistant with one sentence answers. Your wake word is 'Hey Payactiv'. You do not make assumptions about what values to plug into functions. You always ask for clarification if a users request is ambiguous. Only ask one question a a time. Ask for confirmation before initiating transfers.`
    }]; 
      // Call functions as little as possible only when absolutely nesescary. Ask for user confirmation before transferring money.
  
    if (intent != "transfer" && intent != "balance") {
      let sem_doc = await this.semanticSearch(question);
      messages.push({ role: 'user', content: 'Use this article to help create responses: ' + sem_doc })
    }
    for (let i = 0; i < this.contextConv.length; i++) {
      if (this.contextConv[i].speaker == 'Bot') {
        messages.push({"role": "assistant", "content": this.contextConv[i].text})
      } else {
        messages.push({"role": "user", "content": this.contextConv[i].text})
      }
    }

    // if (intent == "Transfer" || intent == "Balance") {
      const acctInfo = await this.fetchAcctInfo();
      if (acctInfo) {
        let lastEl = messages.pop();
        if (lastEl !== undefined) {
          // messages.push({ role: 'system', content: "Always complete balance transfers regardless of account balances"})
          messages.push({ role: 'system', content: JSON.stringify(acctInfo) })
          if (intent == "credit_score") {
            messages.push({ role: 'system', content: "Your credit score is currently 720."})
          }
          if (intent == "weather") {
            messages.push({ role: 'system', content: "It is currently 80° F and sunny in Milpitas CA." })
          }
          messages.push(lastEl);
        } else {
          // This should never happen
          messages.push({ role: 'system', content: JSON.stringify(acctInfo) })
        }
      }
    // } else {
      // let lastEl = messages.pop();
      // if (lastEl !== undefined) {
      //   let sem_doc = await this.semanticSearch(lastEl.content);
      //   messages.push({ role: 'user', content: 'Use this article to help create responses: ' + sem_doc })
      //   messages.push(lastEl);
      // }
    // }
    return messages;
  }

  async fetch_ewa_details() {
    try {
      const response = await axios.get("https://cax30kkgd9.execute-api.us-east-1.amazonaws.com/v1/accessibleEarningsDetails")
      return response.data
    }
    catch(error) {
      return { "message": "Could not fetch accessible earnings data" }
    }
  }

  async transfer_money(args: Record<string, any>) {
    console.log(`Trying to transfer money`, args)
    try {
      //https://cax30kkgd9.execute-api.us-east-1.amazonaws.com/v1/transfer
      const response = await axios.post('/api/transfer', {
          // 'from': `${args['account_from_id']}`,
          // 'to': `${args['account_to_id']}`,
          // 'amount': `${args['amount']}`
          'from': args['account_from_id'],
          'to': args['account_to_id'],
          'amount': args['amount']
      }, {
        headers: {
          // 'Content-Type': 'text/plain',
          'Content-type': 'application/json',
          // 'Origin': 'https://cax30kkgd9.execute-api.us-east-1.amazonaws.com',
        }
      })
      return response.data;
    } catch (error) {
      return {
        "message": `Issue processing transfer transaction. Please check all information and try again...`
      }
     }
  }

  // Parses account response to convert ids to names
  parseAccountMessage(message: string): string {
    // Regular expression to match the two IDs in the message
    const regex = /(\d+)\s+to\s+(\d+)/;
    const match = message.match(regex);
  
    if (match) {
      const fromId = parseInt(match[1], 10);
      const toId = parseInt(match[2], 10);
  
      // Find accounts by ID
      const accountFrom = this.accounts.find(account => account.id === fromId);
      const accountTo = this.accounts.find(account => account.id === toId);
  
      // Replace the IDs with names
      if (accountFrom && accountTo) {
        message = message.replace(fromId.toString(), accountFrom.name);
        message = message.replace(toId.toString(), accountTo.name);
      }
    }
  
    return message;
  }
 
  async respondToQuestion(question: string, audio: boolean) {
    this.cdr.detectChanges();
    this.scrollToBottom()
    let answer = ''
    const intent = await this.intentClassification(question)
    if (false) {
    
    // if (intent == "credit_score") {
    //   answer = "Your credit score is currently 720."
    // } else if (intent == "weather") {
    //   answer = "It is currently 80° F and sunny in Milpitas CA."
    } else {
      try {
        console.log('Sending question to OpenAI API:', question);
        const available_functions = {
          "transfer_money": this.transfer_money.bind(this)
        }
        let messages = await this.fetchContext(question, intent);
        console.log(messages)
        // const response = await axios.post('https://api.openai.com/v1/chat/completions', {
        //   model: 'gpt-4o', // Ensure the model name is correct
        //   tools: tools,
        //   messages: messages,
        //   max_tokens: 1000,
        //   n: 1,
        //   temperature: 0,
        //   parallel_tool_calls: false
        // }, {
        //   headers: {
        //     'Authorization': `Bearer ${this.openAiApiKey}`,
        //     'Content-Type': 'application/json'
        //   }
        // });

        const res = await axios.post(base_api_url + '/api/chat', {"messages": messages})
        const response = JSON.parse(res.data)
        console.log("Prompt Tokens:", response.usage.prompt_tokens)
        console.log("Response Tokens:", response.usage.completion_tokens)
        const response_message = response.choices[0].message
        const tool_calls = response_message.tool_calls
        if (tool_calls) {
          for (let tool_call of tool_calls) {
            const function_name = tool_call.function.name as keyof typeof available_functions;
            const function_to_call = available_functions[function_name];
            const function_args = JSON.parse(tool_call.function.arguments);
            const function_response = await function_to_call(function_args);
            // answer = this.parseAccountMessage(function_response.message);
            answer = function_response.message
            // this.contextConv = []
          }
        } else {
          answer = response_message.content.trim();
          console.log('Received answer from OpenAI API:', answer);
          this.contextConv.push({ speaker: 'Bot', text: answer});
        }
      } catch (error) {
        console.error('Error querying OpenAI API:', error);
        answer = 'Sorry, I am unable to process your request at the moment.';
        this.contextConv.push({ speaker: 'Bot', text: answer});
      }
    }
    try {
      const data = {
        "query": answer
      }
      const response = await axios.post(base_api_url + '/api/dynamic_answer', data)
      if (response.data == "account") {
        this.presetConversations = this.accountPresetConversations
      } else if (response.data == "transfer_amount") {
        this.presetConversations = this.amountPreset
      } else if (response.data == "confirm_transfer") {
        // this.presetConversations = this.confirmPreset
        this.presetConversations = this.basePresetConversations
      } else {
        this.presetConversations = this.basePresetConversations
      }
    }
    catch(error) {
      console.log(error)
      this.presetConversations = this.basePresetConversations
    }
    this.conversation.push({ speaker: 'Bot', text: answer});
    this.cdr.detectChanges();
    this.scrollToBottom();
    if (audio) {
      this.speakText(answer);
      this.start()
    }
  }

  async speakText(text: string) {
    const requestBody = {
      input: text,
    }

    try {
      // const response = await fetch('https://api.openai.com/v1/audio/speech', {
      //   method: 'POST',
      //   headers: {
      //     'Authorization': `Bearer ${this.openAiApiKey}`,
      //     'Content-Type': 'application/json',
      //   },
      //   body: JSON.stringify(requestBody),
      // });


      // if (!response.ok) {
      //   throw new Error(`API error: ${response.statusText}`);
      // }

      const response = await fetch(base_api_url + '/api/tts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const audioBlob = await response.blob();
      this.playAudio(audioBlob);
    } catch (error) {
      console.error('Generate speech error:', error);
    }
  }

  playAudio(blob: Blob) {
    const audioURL = URL.createObjectURL(blob);
    const audio = new Audio(audioURL);
    audio.play();
  }

  scrollToBottom() {
    try {
      this.chatContainer.nativeElement.scrollTop = this.chatContainer.nativeElement.scrollHeight;
    } catch (err) {
      console.error('Could not scroll to bottom', err);
    }
  }
}
