export interface FileInfo {
  name: string
  isDirectory: boolean
}

export interface FileStats {
  isDirectory: boolean
  isFile: boolean
  size: number
  modified: Date
}

declare global {
  interface Window {
    electronAPI: {
      openDirectory: () => Promise<{ canceled: boolean; filePaths: string[] }>
      openFile: () => Promise<{ canceled: boolean; filePaths: string[] }>
      readDirectory: (dirPath: string) => Promise<FileInfo[]>
      getStats: (filePath: string) => Promise<FileStats>
      readFile: (filePath: string) => Promise<string>
      readFileAsDataUrl: (filePath: string) => Promise<string>
    }
  }
}

export {}
