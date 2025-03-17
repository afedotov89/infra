import React from 'react';
import { Container, Typography, Button, Box, Paper } from '@mui/material';
import Link from 'next/link';
import SettingsIcon from '@mui/icons-material/Settings';

export default function Home() {
  return (
    <Container maxWidth="md">
      <Box 
        my={8} 
        display="flex" 
        flexDirection="column" 
        alignItems="center"
      >
        <Typography 
          variant="h3" 
          component="h1" 
          gutterBottom
          align="center"
          sx={{ fontWeight: 'light', mb: 3 }}
        >
          Welcome
        </Typography>
        
        <Paper 
          elevation={0} 
          sx={{ 
            p: 4, 
            width: '100%', 
            maxWidth: 600, 
            mb: 4,
            borderRadius: 2,
            border: '1px solid',
            borderColor: (theme) => theme.palette.mode === 'dark' 
              ? 'rgba(255, 255, 255, 0.1)' 
              : 'rgba(0, 0, 0, 0.1)'
          }}
        >
          <Typography 
            variant="body1" 
            paragraph
            align="center"
            sx={{ fontSize: '1.125rem', mb: 3 }}
          >
            This is a demo application with theme customization.
            You can switch between light, dark and system themes.
          </Typography>

          <Box display="flex" justifyContent="center">
            <Link href="/settings" passHref>
              <Button 
                variant="outlined"
                size="large"
                startIcon={<SettingsIcon />}
                sx={{ px: 3 }}
              >
                Open Settings
              </Button>
            </Link>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
} 