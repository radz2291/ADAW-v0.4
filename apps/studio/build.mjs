import { build } from 'esbuild';
import { mkdir, writeFile } from 'node:fs/promises';
await mkdir('dist', { recursive: true });
const result = await build({ entryPoints: ['studio.js'], outfile: 'dist/studio.js', bundle: true,
  format: 'esm', target: 'es2022', minify: true, legalComments: 'eof', metafile: true });
await writeFile('dist/build.json', JSON.stringify({ entry: 'studio.js', bytes: result.metafile.outputs['dist/studio.js'].bytes,
  dependencies: { '@audio-ui/elements': '0.5.1', '@audio-ui/core': '0.29.1', 'wavesurfer.js': '8.1.0' } }, null, 2) + '\n');
