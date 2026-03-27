import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { LogOut, Home, Calendar, CreditCard, Users } from 'lucide-react'
import RoomManagement from '../components/admin/RoomManagement'
import BookingManagement from '../components/admin/BookingManagement'
import PaymentManagement from '../components/admin/PaymentManagement'
import UserManagement from '../components/admin/UserManagement'

type TabType = 'rooms' | 'bookings' | 'payments' | 'users'

export default function AdminDashboard() {
  const { profile, signOut } = useAuth()
  const [activeTab, setActiveTab] = useState<TabType>('rooms')

  const handleSignOut = async () => {
    await signOut()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
                <Home className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Gestion Réservation</h1>
                <p className="text-xs text-gray-500">Administration</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Admin: {profile?.full_name}</span>
              <button onClick={handleSignOut} className="btn-secondary flex items-center space-x-2">
                <LogOut className="w-4 h-4" />
                <span>Déconnexion</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8">
              <button
                onClick={() => setActiveTab('rooms')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'rooms'
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Home className="w-5 h-5" />
                  <span>Chambres</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('bookings')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'bookings'
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Calendar className="w-5 h-5" />
                  <span>Réservations</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('payments')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'payments'
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <CreditCard className="w-5 h-5" />
                  <span>Paiements</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('users')}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'users'
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Users className="w-5 h-5" />
                  <span>Utilisateurs</span>
                </div>
              </button>
            </nav>
          </div>
        </div>

        <div className="mt-6">
          {activeTab === 'rooms' && <RoomManagement />}
          {activeTab === 'bookings' && <BookingManagement />}
          {activeTab === 'payments' && <PaymentManagement />}
          {activeTab === 'users' && <UserManagement />}
        </div>
      </div>
    </div>
  )
}
