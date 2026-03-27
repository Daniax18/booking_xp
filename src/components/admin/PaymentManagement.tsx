import { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'
import { CreditCard } from 'lucide-react'

interface Payment {
  id: string
  amount: number
  payment_method: string
  status: string
  transaction_id: string | null
  created_at: string
  bookings: {
    id: string
    users: {
      full_name: string
      email: string
    }
    rooms: {
      name: string
    }
  }
}

const statusOptions = ['pending', 'completed', 'failed', 'refunded']
const statusLabels: Record<string, string> = {
  pending: 'En attente',
  completed: 'Complété',
  failed: 'Échoué',
  refunded: 'Remboursé',
}

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  refunded: 'bg-blue-100 text-blue-800',
}

export default function PaymentManagement() {
  const [payments, setPayments] = useState<Payment[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')

  useEffect(() => {
    loadPayments()
  }, [])

  const loadPayments = async () => {
    try {
      const { data, error } = await supabase
        .from('payments')
        .select(`
          *,
          bookings (
            id,
            users (full_name, email),
            rooms (name)
          )
        `)
        .order('created_at', { ascending: false })

      if (error) throw error
      setPayments(data || [])
    } catch (error) {
      console.error('Error loading payments:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStatusChange = async (paymentId: string, newStatus: string) => {
    try {
      const { error } = await supabase
        .from('payments')
        .update({ status: newStatus })
        .eq('id', paymentId)

      if (error) throw error
      loadPayments()
    } catch (error) {
      console.error('Error updating payment:', error)
    }
  }

  const filteredPayments = filter === 'all'
    ? payments
    : payments.filter(p => p.status === filter)

  const totalRevenue = payments
    .filter(p => p.status === 'completed')
    .reduce((sum, p) => sum + p.amount, 0)

  if (loading) {
    return <div className="text-center py-8">Chargement...</div>
  }

  return (
    <div>
      <div className="flex flex-col md:flex-row md:justify-between md:items-center mb-6 space-y-4 md:space-y-0">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Gestion des Paiements</h2>
          <p className="text-lg text-primary-600 font-semibold mt-1">
            Revenus totaux: {totalRevenue.toFixed(2)}€
          </p>
        </div>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="input-field w-48"
        >
          <option value="all">Tous</option>
          <option value="pending">En attente</option>
          <option value="completed">Complétés</option>
          <option value="failed">Échoués</option>
          <option value="refunded">Remboursés</option>
        </select>
      </div>

      <div className="space-y-4">
        {filteredPayments.map((payment) => (
          <div key={payment.id} className="card hover:shadow-lg transition-shadow">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-3">
                  <CreditCard className="w-5 h-5 text-primary-600" />
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">
                      {payment.bookings.rooms.name}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {payment.bookings.users.full_name} ({payment.bookings.users.email})
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                  <div>
                    <p className="text-gray-500">Montant</p>
                    <p className="font-bold text-lg text-primary-600">{payment.amount}€</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Méthode</p>
                    <p className="font-medium">{payment.payment_method}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Date</p>
                    <p className="font-medium">
                      {format(new Date(payment.created_at), 'dd MMM yyyy HH:mm', { locale: fr })}
                    </p>
                  </div>
                </div>

                {payment.transaction_id && (
                  <div className="mt-2">
                    <p className="text-xs text-gray-500">Transaction ID: {payment.transaction_id}</p>
                  </div>
                )}
              </div>

              <div className="md:ml-6 mt-4 md:mt-0">
                <select
                  value={payment.status}
                  onChange={(e) => handleStatusChange(payment.id, e.target.value)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium ${statusColors[payment.status]} border-none cursor-pointer`}
                >
                  {statusOptions.map((status) => (
                    <option key={status} value={status}>
                      {statusLabels[status]}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        ))}

        {filteredPayments.length === 0 && (
          <div className="card text-center py-12">
            <CreditCard className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Aucun paiement trouvé</p>
          </div>
        )}
      </div>
    </div>
  )
}
