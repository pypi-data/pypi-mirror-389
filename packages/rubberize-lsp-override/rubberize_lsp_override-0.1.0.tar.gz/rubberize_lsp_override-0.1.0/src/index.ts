import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { ILSPCodeOverridesManager } from '@jupyter-lsp/jupyterlab-lsp';

/**
 * A plugin that registers an override for %%tap cell magics.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: '@rubberize/lsp-override:plugin',
  autoStart: true,
  requires: [ILSPCodeOverridesManager],
  activate: (
    _app: JupyterFrontEnd,
    overridesManager: ILSPCodeOverridesManager
  ) => {
    overridesManager.register(
      {
        pattern: '^%%(tap|ast)(?![^\\n]*--dead)([^\n]*)\\n([\\s\\S]*)',
        replacement: (match, name, args, content) => {
          const escapedArgs = args.replace(/(["\\])/g, '\\$1').trim();
          const safeContent = content.replace(/"""/g, '\\"\\"\\"');
          return `# START_CELL_MAGIC("${name}", "${escapedArgs}")\n${safeContent}\n# END_CELL_MAGIC`;
        },
        scope: 'cell',
        reverse: {
          pattern:
            '^# START_CELL_MAGIC\\("(tap|ast)", "(.*?)"\\)\\n([\\s\\S]*)\\n# END_CELL_MAGIC$',
          replacement: (match, name, args, content) => {
            const unescapedArgs = args.replace(/\\"/g, '"');
            return `%%${name} ${unescapedArgs}\n${content}`;
          },
          scope: 'cell'
        }
      },
      'python'
    );
    // console.log('Registered LSP override for %%tap cells');
  }
};

export default extension;
