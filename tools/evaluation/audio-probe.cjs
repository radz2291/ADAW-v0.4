// Independent measurement at the actual Web Audio output connection. No product hooks.
module.exports = async function installAudioProbe(page, silentSink=false) {
  await page.addInitScript((silentSink) => {
    window.__independentAudio = [];
    const original = AudioNode.prototype.connect;
    AudioNode.prototype.connect = function(destination, ...args) {
      if (destination instanceof AudioDestinationNode) {
        if(silentSink) {
          const sink=this.context.createGain();sink.gain.value=0;
          original.call(this,sink);original.call(sink,destination);
        } else original.call(this,destination,...args);
        const analyser = this.context.createAnalyser();
        analyser.fftSize = 2048;
        original.call(this, analyser);
        const entry = {node:this, context:this.context, analyser};
        window.__independentAudio.push(entry);
        return destination;
      }
      return original.call(this, destination, ...args);
    };
    window.__independentRead = () => window.__independentAudio.map(entry => {
      const data=new Float32Array(entry.analyser.fftSize);
      entry.analyser.getFloatTimeDomainData(data);
      let sum=0,peak=0;for(const sample of data){sum+=sample*sample;peak=Math.max(peak,Math.abs(sample));}
      return {rms:Math.sqrt(sum/data.length),peak,time:performance.now(),state:entry.context.state};
    });
  },silentSink);
};
