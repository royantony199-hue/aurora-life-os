import React from 'react';

export function TestComponent() {
  return (
    <div className="mobile-card">
      <h2 className="text-xl font-bold text-gray-800 mb-4">🧪 Component Test</h2>
      <div className="space-y-4">
        <div className="bg-green-100 p-4 rounded-lg">
          <h3 className="font-semibold text-green-800">✅ This component is working!</h3>
          <p className="text-green-700 mt-2">If you can see this, the tab navigation is functioning properly.</p>
        </div>
        
        <div className="bg-blue-100 p-4 rounded-lg">
          <h3 className="font-semibold text-blue-800">🔧 Debug Info</h3>
          <ul className="text-blue-700 mt-2 text-sm">
            <li>• Component rendered successfully</li>
            <li>• No TypeScript errors</li>
            <li>• Mobile styling applied</li>
            <li>• Error boundary protecting</li>
          </ul>
        </div>
        
        <div className="bg-yellow-100 p-4 rounded-lg">
          <h3 className="font-semibold text-yellow-800">💡 Next Steps</h3>
          <p className="text-yellow-700 mt-2">Try switching between different tabs. Each should load without going blank.</p>
        </div>
      </div>
    </div>
  );
}