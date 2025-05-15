import { NextRequest, NextResponse } from 'next/server';

// CORS middleware to handle requests from different origins
export function corsMiddleware(handler: (req: NextRequest) => Promise<NextResponse>) {
  return async (req: NextRequest) => {
    console.log('[DEBUG] Handling CORS for request to:', req.url);
    
    // Get the response from the handler
    const response = await handler(req);
    
    // Add CORS headers
    response.headers.set('Access-Control-Allow-Origin', '*');
    response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    
    // For preflight requests
    if (req.method === 'OPTIONS') {
      console.log('[DEBUG] Handling OPTIONS preflight request');
      return new NextResponse(null, {
        status: 204,
        headers: response.headers
      });
    }
    
    return response;
  };
}