import importlib.metadata

__version__ = importlib.metadata.version("moboard") 

import anywidget
import traitlets

class KeystrokeWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      let keyDiv = document.createElement('div');
      keyDiv.style.padding = '20px';
      keyDiv.style.border = '2px solid #4CAF50';
      keyDiv.style.borderRadius = '8px';
      keyDiv.style.textAlign = 'center';
      keyDiv.style.fontFamily = 'monospace';
      keyDiv.style.fontSize = '16px';
      keyDiv.innerHTML = 'Click here and press any key...';
      keyDiv.tabIndex = 0; // Make div focusable
      
      let lastKeyInfo = document.createElement('div');
      lastKeyInfo.style.marginTop = '10px';
      lastKeyInfo.style.fontSize = '14px';
      lastKeyInfo.style.color = '#666';
      
      el.appendChild(keyDiv);
      el.appendChild(lastKeyInfo);
      
      keyDiv.addEventListener('keydown', (event) => {
        event.preventDefault(); // Prevent default behavior
        
        const keyInfo = {
          key: event.key,
          code: event.code,
          ctrlKey: event.ctrlKey,
          shiftKey: event.shiftKey,
          altKey: event.altKey,
          metaKey: event.metaKey,
          timestamp: Date.now()
        };
        
        model.set('last_key', keyInfo);
        model.save_changes();
        
        // Update display
        let modifiers = [];
        if (event.ctrlKey) modifiers.push('Ctrl');
        if (event.shiftKey) modifiers.push('Shift');
        if (event.altKey) modifiers.push('Alt');
        if (event.metaKey) modifiers.push('Meta');
        
        let modStr = modifiers.length > 0 ? modifiers.join('+') + '+' : '';
        keyDiv.innerHTML = `<strong>Key Pressed:</strong> ${modStr}${event.key}`;
        lastKeyInfo.innerHTML = `Code: ${event.code}`;
        
        // Flash effect
        keyDiv.style.backgroundColor = '#e8f5e9';
        setTimeout(() => {
          keyDiv.style.backgroundColor = 'transparent';
        }, 200);
      });
    }

    export default {render}
    """
    
    last_key = traitlets.Dict({}).tag(sync=True)
