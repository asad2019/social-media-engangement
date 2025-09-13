import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Card, { CardBody, CardHeader } from '../../components/ui/Card';

const TwoFactorAuthPage: React.FC = () => {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [resendLoading, setResendLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // TODO: Implement actual 2FA verification API call
      console.log('2FA verification with code:', code);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Redirect to dashboard
      window.location.href = '/dashboard';
    } catch (err) {
      setError('Invalid verification code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    setResendLoading(true);
    try {
      // TODO: Implement resend code API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      // Show success message
    } catch (err) {
      setError('Failed to resend code. Please try again.');
    } finally {
      setResendLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h2 className="mt-6 text-3xl font-bold text-neutral-900">
            Two-factor authentication
          </h2>
          <p className="mt-2 text-sm text-neutral-600">
            Enter the verification code from your authenticator app
          </p>
        </div>

        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-neutral-900">Verify your identity</h3>
            <p className="text-sm text-neutral-600">Enter the 6-digit code from your authenticator app</p>
          </CardHeader>
          <CardBody>
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="alert alert-error">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-error-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-error-800">{error}</p>
                    </div>
                  </div>
                </div>
              )}

              <div className="text-center">
                <Input
                  label="Verification code"
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  required
                  placeholder="000000"
                  maxLength={6}
                  className="text-center text-2xl tracking-widest"
                />
                <p className="mt-2 text-sm text-neutral-500">
                  Enter the 6-digit code from your authenticator app
                </p>
              </div>

              <Button
                type="submit"
                loading={loading}
                fullWidth
                size="lg"
                disabled={code.length !== 6}
              >
                Verify code
              </Button>
            </form>

            <div className="mt-6 text-center space-y-4">
              <button
                onClick={handleResendCode}
                disabled={resendLoading}
                className="text-sm text-primary-600 hover:text-primary-500 disabled:opacity-50"
              >
                {resendLoading ? 'Sending...' : "Didn't receive a code? Resend"}
              </button>
              
              <div className="text-sm text-neutral-500">
                Having trouble?{' '}
                <Link to="/support" className="text-primary-600 hover:text-primary-500">
                  Contact support
                </Link>
              </div>
            </div>
          </CardBody>
        </Card>

        <div className="text-center">
          <Link to="/login" className="text-sm text-primary-600 hover:text-primary-500">
            ← Back to login
          </Link>
        </div>
      </div>
    </div>
  );
};

export default TwoFactorAuthPage;
