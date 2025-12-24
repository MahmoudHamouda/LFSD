import React, { useState } from 'react';
import styles from './FileUploadProgress.module.css';

export interface FileUploadStatus {
    filename: string;
    status: 'pending' | 'uploading' | 'parsing' | 'complete' | 'error' | 'paused';
    progress: number;
    error?: string;
    transactionCount?: number;
    sessionId?: string;
}

export interface FileUploadProgressProps {
    onComplete: (sessionIds: string[]) => void;
    onError?: (error: string) => void;
    files?: FileUploadStatus[];
    onFilesChange?: React.Dispatch<React.SetStateAction<FileUploadStatus[]>>;
    uploadUrl?: string;
    title?: string;
    description?: string;
    onRemove?: (file: FileUploadStatus) => void;
}

export const FileUploadProgress: React.FC<FileUploadProgressProps> = ({
    onComplete,
    onError,
    files: controlledFiles,
    onFilesChange,
    uploadUrl = '/api/onboarding/upload-statement',
    title = "Upload Bank Statements",
    description = "Drag and drop files here, or click to browse",
    onRemove
}) => {
    // ... state ...
    const [internalFiles, setInternalFiles] = useState<FileUploadStatus[]>([]);

    // Use controlled state if provided, otherwise internal state
    const files = controlledFiles || internalFiles;
    const setFiles = (newFiles: React.SetStateAction<FileUploadStatus[]>) => {
        if (onFilesChange) {
            onFilesChange(newFiles);
        } else {
            setInternalFiles(newFiles);
        }
    };

    // ... rest of component ...

    // (I need to jump to the return statement to replace the text)
    // Wait, I can't replace scattered chunks easily with replace_file.
    // I will use replace_file_content to replace the interface and destructuring first.

    // ...
    // Actually, I can do it in two chunks or one large one if I'm careful.
    // Let's do the interface and destructuring first.


    console.log('FileUploadProgress Render');
    React.useEffect(() => {
        console.log('FileUploadProgress MOUNT');
        return () => console.log('FileUploadProgress UNMOUNT');
    }, []);
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);

    const fileToBase64 = (file: File): Promise<string> => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                const result = reader.result as string;
                const base64 = result.includes(',') ? result.split(',')[1] : result;
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    };

    const activeFilesRef = React.useRef<File[]>([]);
    const abortControllerRef = React.useRef<AbortController | null>(null);

    const processFiles = async (filesToProcess: File[]) => {
        setIsUploading(true);

        // Create new abort controller
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }
        const controller = new AbortController();
        abortControllerRef.current = controller;

        try {
            const filesData = await Promise.all(
                filesToProcess.map(async (file) => ({
                    filename: file.name,
                    content: await fileToBase64(file)
                }))
            );

            // Check if aborted during file reading
            if (controller.signal.aborted) return;

            setFiles(prev => prev.map(f => ({
                ...f,
                status: 'uploading' as const,
                progress: 20,
                error: undefined
            })));

            const response = await fetch(uploadUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ files: filesData }),
                signal: controller.signal
            });

            if (!response.ok) {
                let errorMessage = 'Upload failed';
                try {
                    const error = await response.json();
                    errorMessage = error.detail || errorMessage;
                } catch {
                    errorMessage = `Server error (${response.status}). Please contact support@viv.com`;
                }
                throw new Error(errorMessage);
            }

            let result;
            try {
                result = await response.json();
            } catch {
                throw new Error("Invalid server response. Please contact support@viv.com");
            }

            setFiles(prev => prev.map(f => ({ ...f, status: 'parsing' as const, progress: 60 })));

            const sessionIds = result.files
                ?.filter((f: any) => f.status === 'success')
                .map((f: any) => f.session_id) || [];

            setFiles(prev => prev.map(file => {
                const fileResult = result.files?.find((r: any) => r.filename === file.filename);

                if (!fileResult) {
                    return { ...file, status: 'error' as const, error: 'No result returned' };
                }

                if (fileResult.status === 'success') {
                    return {
                        ...file,
                        status: 'complete' as const,
                        progress: 100,
                        transactionCount: fileResult.transaction_count,
                        sessionId: fileResult.session_id,
                        error: undefined
                    };
                } else {
                    return {
                        ...file,
                        status: 'error' as const,
                        error: fileResult.error || 'Upload failed'
                    };
                }
            }));
            setIsUploading(false);
            onComplete(sessionIds);

        } catch (error: any) {
            if (error.name === 'AbortError') {
                console.log('Upload aborted');
                setFiles(prev => prev.map(f => ({ ...f, status: 'paused' as const, error: 'Upload paused' })));
            } else {
                console.error('Upload error:', error);

                let userMessage = error.message;
                // Catch technical JSON/fetch errors and make them friendly
                if (
                    userMessage.includes("JSON") ||
                    userMessage.includes("json") ||
                    userMessage.includes("Failed to execute") ||
                    userMessage.includes("NetworkError")
                ) {
                    userMessage = "System error. Please contact support@viv.com";
                }

                setFiles(prev => prev.map(f => ({
                    ...f,
                    status: 'error' as const,
                    error: userMessage
                })));
                if (onError) {
                    onError(userMessage);
                }
            }
            setIsUploading(false);
        } finally {
            abortControllerRef.current = null;
        }
    };

    const handleFileSelect = async (selectedFiles: FileList | null) => {
        if (!selectedFiles || selectedFiles.length === 0) return;

        const fileArray = Array.from(selectedFiles);
        activeFilesRef.current = fileArray; // Store files for retry

        const initialStatuses: FileUploadStatus[] = fileArray.map(f => ({
            filename: f.name,
            status: 'pending',
            progress: 0
        }));

        setFiles(initialStatuses);
        await processFiles(fileArray);
    };

    const togglePause = () => {
        if (isUploading) {
            // Pause
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        } else {
            // Resume
            if (activeFilesRef.current.length > 0) {
                processFiles(activeFilesRef.current);
            }
        }
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        handleFileSelect(e.dataTransfer.files);
    };

    const getStatusIcon = (status: FileUploadStatus['status']) => {
        switch (status) {
            case 'complete':
                return '✓';
            case 'error':
                return '⟳';
            case 'paused':
                return '▶';
            case 'uploading':
            case 'parsing':
                return '⏸';
            default:
                return '○';
        }
    };

    const getStatusText = (file: FileUploadStatus) => {
        switch (file.status) {
            case 'pending':
                return 'Waiting...';
            case 'uploading':
                return 'Uploading...';
            case 'parsing':
                return 'Parsing document...';
            case 'complete':
                return file.transactionCount
                    ? `Complete (${file.transactionCount} transactions)`
                    : 'Upload Complete';
            case 'error':
                return `Error: ${file.error}`;
            case 'paused':
                return 'Paused';
        }
    };

    const removeFile = (index: number) => {
        const fileToRemove = files[index];
        const newFiles = [...files];
        newFiles.splice(index, 1);
        setFiles(newFiles);
        if (onRemove) {
            onRemove(fileToRemove);
        }
    };

    return (
        <div className={styles.container}>
            {files.length === 0 ? (
                <div
                    className={`${styles.dropZone} ${isDragging ? styles.dragging : ''}`}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={() => document.getElementById('file-input')?.click()}
                >
                    <div className={styles.dropZoneContent}>
                        <div className={styles.uploadIcon}>📄</div>
                        <h3>{title}</h3>
                        <p>{description}</p>
                        <p className={styles.supportedFormats}>Supports: PDF, CSV, XLS, XLSX</p>
                        <p className={styles.multiFileHint}>You can upload multiple files at once</p>
                    </div>
                    <input
                        id="file-input"
                        type="file"
                        multiple
                        accept=".pdf,.csv,.xls,.xlsx"
                        onChange={(e) => handleFileSelect(e.target.files)}
                        style={{ display: 'none' }}
                    />
                </div>
            ) : (
                <div className={styles.fileList}>
                    <h3>Uploading {files.length} file{files.length > 1 ? 's' : ''}</h3>
                    {files.map((file, index) => (
                        <div key={index} className={styles.fileItem}>
                            <div className={styles.fileHeader}>
                                <span
                                    className={styles.fileIcon}
                                    onClick={togglePause}
                                    style={{ cursor: 'pointer' }}
                                >
                                    {getStatusIcon(file.status)}
                                </span>
                                <span className={styles.fileName}>{file.filename}</span>
                                <span className={styles.fileStatus}>{getStatusText(file)}</span>
                                <button
                                    onClick={() => removeFile(index)}
                                    style={{
                                        border: 'none',
                                        background: 'none',
                                        color: '#94a3b8',
                                        cursor: 'pointer',
                                        fontSize: '1.2rem',
                                        marginLeft: 'auto', // Push to right
                                        padding: '0.2rem'
                                    }}
                                    title="Remove file"
                                >
                                    ×
                                </button>
                            </div>
                            <div className={styles.progressBar}>
                                <div
                                    className={`${styles.progressFill} ${styles[file.status]}`}
                                    style={{ width: `${file.progress}%` }}
                                />
                            </div>
                            {file.error && (
                                <div className={styles.errorMessage}>{file.error}</div>
                            )}
                        </div>
                    ))}
                    {!isUploading && (
                        <button
                            className={styles.addMoreButton}
                            onClick={() => setFiles([])}
                        >
                            Upload More Files
                        </button>
                    )}
                </div>
            )}
        </div>
    );
};
