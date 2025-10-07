import React, { useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { WebView } from 'react-native-webview';

interface VideoStreamProps {
  streamUrl: string;
  width?: number;
  height?: number;
}

const VideoStream: React.FC<VideoStreamProps> = ({ 
  streamUrl, 
  width = 320, 
  height = 240 
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  // MJPEG 스트림을 위한 HTML 템플릿
  const htmlContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
      <style>
        body {
          margin: 0;
          padding: 0;
          background-color: #000;
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100vh;
          overflow: hidden;
        }
        img {
          width: 100%;
          height: 100%;
          object-fit: contain;
        }
        .error {
          color: white;
          text-align: center;
          font-family: Arial, sans-serif;
        }
      </style>
    </head>
    <body>
      <img src="${streamUrl}" 
           onerror="this.style.display='none'; document.body.innerHTML='<div class=error>❌<br/>스트림을 불러올 수 없습니다</div>';" />
    </body>
    </html>
  `;

  return (
    <View style={[styles.container, { width, height }]}>
      {loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#4A90E2" />
          <Text style={styles.loadingText}>스트림 로딩 중...</Text>
        </View>
      )}
      <WebView
        source={{ html: htmlContent }}
        style={styles.webview}
        onLoadStart={() => setLoading(true)}
        onLoad={() => setLoading(false)}
        onError={() => {
          setLoading(false);
          setError(true);
        }}
        scrollEnabled={false}
        bounces={false}
        scalesPageToFit={true}
        javaScriptEnabled={true}
        domStorageEnabled={true}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#000',
    borderRadius: 10,
    overflow: 'hidden',
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  webview: {
    backgroundColor: '#000',
    flex: 1,
    width: '100%',
    height: '100%',
  },
  loadingContainer: {
    position: 'absolute',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
  },
  loadingText: {
    color: '#fff',
    marginTop: 10,
    fontSize: 14,
  },
});

export default VideoStream;
