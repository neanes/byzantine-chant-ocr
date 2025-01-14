import { spawn } from 'child_process';

export interface OcrLaunchOptions {
  deskew?: boolean;
  despeckle?: boolean;
  close?: boolean;
  splitLeftRight?: boolean;
}

export async function launchOcr(
  scriptPath: string,
  imagePath: string,
  outputPath: string,
  options: OcrLaunchOptions,
) {
  const args = [scriptPath, imagePath, '-o', outputPath];

  if (options.splitLeftRight) {
    args.push('--split-lr');
  }

  if (options.deskew) {
    args.push('--deskew');
  }

  if (options.despeckle) {
    args.push('--despeckle');
  }

  if (options.close) {
    args.push('--close');
  }

  const process = spawn('python', args);

  //let output = '';
  //let error = '';

  // process.stdout.on('data', function (data: string) {
  //   output += data;
  // });

  process.stderr.on('data', function (data) {
    //error += data;
    console.log(data.toString());
  });

  await new Promise((resolve) => {
    process.on('close', resolve);
  });

  //console.log(error);

  //return output;
}
