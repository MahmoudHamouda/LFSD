import React from 'react';
import { Stack, Text, PrimaryButton, DefaultButton, TextField, IStackStyles, Icon } from '@fluentui/react';

const sectionStyles: IStackStyles = {
    root: {
        background: 'white',
        borderRadius: '8px',
        padding: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        marginTop: '20px',
    },
};

export const ConnectCalendar: React.FC = () => {
    const handleConnect = async () => {
        try {
            const response = await fetch('/api/calendar/connect', { method: 'POST' });
            if (response.ok) {
                alert("Calendar connected successfully!");
            } else {
                alert("Failed to connect calendar. Check console.");
            }
        } catch (error) {
            console.error("Error connecting calendar:", error);
            alert("Error connecting calendar.");
        }
    };

    return (
        <Stack styles={sectionStyles} tokens={{ childrenGap: 10 }}>
            <Text variant="large" style={{ fontWeight: 600 }}>Connect Calendar</Text>
            <Text variant="small">Sync your Google or Outlook calendar to get started.</Text>
            <Stack horizontal tokens={{ childrenGap: 10 }}>
                <PrimaryButton text="Connect Google Calendar" iconProps={{ iconName: 'Calendar' }} onClick={handleConnect} />
                <DefaultButton text="Connect Outlook" iconProps={{ iconName: 'OutlookLogo' }} />
            </Stack>
        </Stack>
    );
};

export const AddEventForm: React.FC = () => {
    return (
        <Stack styles={sectionStyles} tokens={{ childrenGap: 10 }}>
            <Text variant="large" style={{ fontWeight: 600 }}>Add Manual Event</Text>
            <Stack tokens={{ childrenGap: 10 }}>
                <TextField label="Event Title" placeholder="e.g., Deep Work" />
                <Stack horizontal tokens={{ childrenGap: 10 }}>
                    <TextField label="Start Time" type="time" />
                    <TextField label="End Time" type="time" />
                </Stack>
                <PrimaryButton text="Add Event" />
            </Stack>
        </Stack>
    );
};

export const UploadSchedule: React.FC = () => {
    return (
        <Stack styles={sectionStyles} tokens={{ childrenGap: 10 }}>
            <Text variant="large" style={{ fontWeight: 600 }}>Upload Schedule</Text>
            <div style={{
                border: '2px dashed #0078d4',
                borderRadius: '4px',
                padding: '20px',
                textAlign: 'center',
                cursor: 'pointer',
                backgroundColor: '#f3f9fd'
            }}>
                <Icon iconName="CloudUpload" style={{ fontSize: '24px', color: '#0078d4', marginBottom: '10px' }} />
                <Text block variant="medium">Drag & drop a PDF or image of your schedule here</Text>
                <Text block variant="small" style={{ color: '#666' }}>or click to browse</Text>
            </div>
        </Stack>
    );
};
