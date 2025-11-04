/* Funções de flood (multi-semente) para DrawTree/mtviz.
 * Define window.DrawTreeFlood com API: floodExactMulti, floodThreshold, use(name), register.
 */
(function(){
  function getParams(image_source, alpha_ctrl){
    const num_cols = image_source.data.numCols[0];
    const num_rows = image_source.data.numRows[0];
    const bufOrig  = image_source.data.imageOrig[0];
    const overBuf  = image_source.data.overlay[0];
    const visited  = image_source.data.visited[0];
    const a  = (alpha_ctrl ? (alpha_ctrl.value|0) : 100);
    const rp = (255 * a / 255) | 0;
    const newVal = (rp<<24) | (0<<16) | (0<<8) | a;
    return { num_cols, num_rows, bufOrig, overBuf, visited, newVal };
  }

  function floodExactMulti(image_source, alpha_ctrl, seeds, nbr){
    const { num_cols, num_rows, bufOrig, overBuf, visited, newVal } = getParams(image_source, alpha_ctrl);
    overBuf.fill(0); visited.fill(0);
    const N = num_cols * num_rows;
    const defaultNbr8 = [[-1,-1],[-1,0],[-1,1],[0,-1],[0,1],[1,-1],[1,0],[1,1]];
    const defaultNbr4 = [[-1,0],[1,0],[0,-1],[0,1]];
    const nb = (Array.isArray(nbr) && nbr.length) ? nbr : ((nbr === 4) ? defaultNbr4 : defaultNbr8);
    for (let si = 0; si < seeds.length; si++){
      const seedIdx = seeds[si] | 0;
      if (seedIdx < 0 || seedIdx >= N) continue;
      if (visited[seedIdx]) { overBuf[seedIdx] = newVal; continue; }
      const target = bufOrig[seedIdx]; if (!Number.isFinite(target)) continue;
      const stack = [seedIdx]; visited[seedIdx] = 1;
      while (stack.length){
        const k0 = stack.pop(); const r0 = (k0 / num_cols) | 0; const c0 = k0 % num_cols;
        overBuf[k0] = newVal;
        for (let j = 0; j < nb.length; j++){
          const rr = r0 + nb[j][0], cc = c0 + nb[j][1];
          if (rr < 0 || rr >= num_rows || cc < 0 || cc >= num_cols) continue;
          const kk = rr * num_cols + cc; if (visited[kk]) continue;
          if (bufOrig[kk] === target){ visited[kk] = 1; stack.push(kk); }
        }
      }
    }
    image_source.change.emit();
  }

  function floodThreshold(image_source, alpha_ctrl, seeds, nbr){
    const { num_cols, num_rows, bufOrig, overBuf, visited, newVal } = getParams(image_source, alpha_ctrl);
    overBuf.fill(0); visited.fill(0);
    const N = num_cols * num_rows; if (!seeds || !seeds.length){ image_source.change.emit(); return; }
    const pol = (window.DrawTreeFlood && window.DrawTreeFlood.polarity === 255) ? 255 : 0;
    let seedVals = [];
    for (let si = 0; si < seeds.length; si++){
      const k = seeds[si] | 0; if (k < 0 || k >= N) continue; const v = bufOrig[k]; if (Number.isFinite(v)) seedVals.push(v);
    }
    if (!seedVals.length){ image_source.change.emit(); return; }
    const thr = (pol === 255) ? Math.min.apply(null, seedVals) : Math.max.apply(null, seedVals);
    const accept = (v) => Number.isFinite(v) && ((pol === 255 && v >= thr) || (pol === 0 && v <= thr));
    const defaultNbr8 = [[-1,-1],[-1,0],[-1,1],[0,-1],[0,1],[1,-1],[1,0],[1,1]];
    const defaultNbr4 = [[-1,0],[1,0],[0,-1],[0,1]];
    const nb = (Array.isArray(nbr) && nbr.length) ? nbr : ((nbr === 4) ? defaultNbr4 : defaultNbr8);
    const stack = [];
    for (let si = 0; si < seeds.length; si++){
      const k = seeds[si] | 0; if (k < 0 || k >= N) continue;
      if (!visited[k] && accept(bufOrig[k])){ visited[k] = 1; overBuf[k] = newVal; stack.push(k); }
    }
    while (stack.length){
      const k0 = stack.pop(); const r0 = (k0 / num_cols) | 0; const c0 = k0 % num_cols;
      for (let j = 0; j < nb.length; j++){
        const rr = r0 + nb[j][0], cc = c0 + nb[j][1];
        if (rr < 0 || rr >= num_rows || cc < 0 || cc >= num_cols) continue;
        const kk = rr * num_cols + cc; if (visited[kk]) continue;
        const v = bufOrig[kk]; if (accept(v)) { visited[kk] = 1; overBuf[kk] = newVal; stack.push(kk); }
      }
    }
    image_source.change.emit();
  }

  function wireAPI(){
    const API = window.DrawTreeFlood || {};
    API.floodExactMulti = floodExactMulti;
    API.floodThreshold = floodThreshold;
    if (!(API.polarity === 0 || API.polarity === 255)) API.polarity = 0;
    API.register = function(name, fn){ if (typeof fn === 'function') API[name] = fn; };
    API.use = function(name){ const fn = (name && typeof API[name] === 'function') ? API[name] : API.floodExactMulti; API.run = fn; window.runFloodMulti = fn; };
    if (typeof API.run !== 'function') API.use('floodExactMulti');
    window.DrawTreeFlood = API; if (typeof window.runFloodMulti !== 'function') window.runFloodMulti = API.run;
  }

  if (typeof window !== 'undefined') wireAPI();
})();
