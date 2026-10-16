const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('organelleScope', { runtime: () => ipcRenderer.invoke('organelle:runtime') });
