import React from 'react';
import { Link } from 'react-router-dom';
import Button from '../components/ui/Button';
import Card, { CardBody } from '../components/ui/Card';

const HomePage: React.FC = () => {
  const features = [
    {
      icon: '🚀',
      title: 'Instant Engagement',
      description: 'Get real engagement from authentic users within minutes of launching your campaign.'
    },
    {
      icon: '🔒',
      title: 'Secure & Verified',
      description: 'All engagements are verified through our multi-layer verification system ensuring authenticity.'
    },
    {
      icon: '💰',
      title: 'Fair Pricing',
      description: 'Transparent pricing with no hidden fees. Pay only for verified completions.'
    },
    {
      icon: '📊',
      title: 'Real-time Analytics',
      description: 'Track your campaign performance with detailed analytics and insights.'
    },
    {
      icon: '🎯',
      title: 'Targeted Reach',
      description: 'Reach your specific audience with advanced targeting options.'
    },
    {
      icon: '⚡',
      title: 'Fast Processing',
      description: 'Quick verification and instant payouts for all completed tasks.'
    }
  ];

  const platforms = [
    { name: 'Instagram', icon: '📷', color: 'bg-gradient-to-r from-pink-500 to-purple-600' },
    { name: 'Twitter', icon: '🐦', color: 'bg-gradient-to-r from-blue-400 to-blue-600' },
    { name: 'Facebook', icon: '📘', color: 'bg-gradient-to-r from-blue-600 to-blue-800' },
    { name: 'TikTok', icon: '🎵', color: 'bg-gradient-to-r from-black to-gray-800' },
    { name: 'YouTube', icon: '📺', color: 'bg-gradient-to-r from-red-500 to-red-700' },
    { name: 'LinkedIn', icon: '💼', color: 'bg-gradient-to-r from-blue-700 to-blue-900' }
  ];

  const stats = [
    { number: '10K+', label: 'Active Users' },
    { number: '50K+', label: 'Completed Tasks' },
    { number: '$100K+', label: 'Total Payouts' },
    { number: '99.9%', label: 'Uptime' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-primary-50">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-primary-600/10 to-secondary-600/10"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-neutral-900 mb-6">
              The Future of{' '}
              <span className="text-gradient">Social Engagement</span>
            </h1>
            <p className="text-xl text-neutral-600 mb-8 max-w-3xl mx-auto">
              Connect Promoters with Earners in a secure, transparent marketplace. 
              Get real engagement for your content while earning money for authentic interactions.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/register">
                <Button size="xl" className="shadow-glow">
                  Get Started Free
                </Button>
              </Link>
              <Link to="/login">
                <Button variant="secondary" size="xl">
                  Sign In
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl md:text-4xl font-bold text-primary-600 mb-2">
                  {stat.number}
                </div>
                <div className="text-neutral-600">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-neutral-900 mb-4">
              Why Choose Our Platform?
            </h2>
            <p className="text-xl text-neutral-600 max-w-2xl mx-auto">
              We provide the most secure and efficient way to connect content creators with authentic engagement.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index} hover className="text-center">
                <CardBody>
                  <div className="text-4xl mb-4">{feature.icon}</div>
                  <h3 className="text-xl font-semibold text-neutral-900 mb-3">
                    {feature.title}
                  </h3>
                  <p className="text-neutral-600">
                    {feature.description}
                  </p>
                </CardBody>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Platforms Section */}
      <section className="py-20 bg-gradient-to-r from-primary-50 to-secondary-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-neutral-900 mb-4">
              Supported Platforms
            </h2>
            <p className="text-xl text-neutral-600 max-w-2xl mx-auto">
              Connect with audiences across all major social media platforms.
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
            {platforms.map((platform, index) => (
              <Card key={index} hover className="text-center">
                <CardBody>
                  <div className={`w-16 h-16 mx-auto mb-4 rounded-xl ${platform.color} flex items-center justify-center text-2xl`}>
                    {platform.icon}
                  </div>
                  <h3 className="font-semibold text-neutral-900">
                    {platform.name}
                  </h3>
                </CardBody>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-neutral-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-neutral-600 max-w-2xl mx-auto">
              Simple steps to get started with our platform.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-2xl font-bold text-primary-600">1</span>
              </div>
              <h3 className="text-xl font-semibold text-neutral-900 mb-3">
                Create Account
              </h3>
              <p className="text-neutral-600">
                Sign up as a Promoter or Earner and complete your profile verification.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-secondary-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-2xl font-bold text-secondary-600">2</span>
              </div>
              <h3 className="text-xl font-semibold text-neutral-900 mb-3">
                Launch Campaign
              </h3>
              <p className="text-neutral-600">
                Promoters create campaigns with specific engagement requirements and budget.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-accent-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-2xl font-bold text-accent-600">3</span>
              </div>
              <h3 className="text-xl font-semibold text-neutral-900 mb-3">
                Earn & Verify
              </h3>
              <p className="text-neutral-600">
                Earners complete tasks and get verified through our secure system.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-primary-600 to-secondary-600">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Ready to Get Started?
          </h2>
          <p className="text-xl text-primary-100 mb-8">
            Join thousands of users who are already earning and growing their social presence.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register">
              <Button variant="secondary" size="xl">
                Start Earning Today
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="ghost" size="xl" className="text-white border-white hover:bg-white hover:text-primary-600">
                Sign In
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-neutral-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <h3 className="text-xl font-bold mb-4">Engagement Platform</h3>
              <p className="text-neutral-400">
                The most secure and transparent marketplace for social media engagement.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">For Promoters</h4>
              <ul className="space-y-2 text-neutral-400">
                <li><Link to="/campaigns" className="hover:text-white">Create Campaigns</Link></li>
                <li><Link to="/analytics" className="hover:text-white">Analytics</Link></li>
                <li><Link to="/pricing" className="hover:text-white">Pricing</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">For Earners</h4>
              <ul className="space-y-2 text-neutral-400">
                <li><Link to="/jobs" className="hover:text-white">Available Jobs</Link></li>
                <li><Link to="/wallet" className="hover:text-white">Wallet</Link></li>
                <li><Link to="/profile" className="hover:text-white">Profile</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Support</h4>
              <ul className="space-y-2 text-neutral-400">
                <li><Link to="/help" className="hover:text-white">Help Center</Link></li>
                <li><Link to="/contact" className="hover:text-white">Contact Us</Link></li>
                <li><Link to="/terms" className="hover:text-white">Terms of Service</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-neutral-800 mt-8 pt-8 text-center text-neutral-400">
            <p>&copy; 2024 Engagement Platform. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;