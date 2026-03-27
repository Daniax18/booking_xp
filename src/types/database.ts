export interface Database {
  public: {
    Tables: {
      users: {
        Row: {
          id: string
          email: string
          full_name: string
          role: 'client' | 'admin'
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          email: string
          full_name: string
          role?: 'client' | 'admin'
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          email?: string
          full_name?: string
          role?: 'client' | 'admin'
          created_at?: string
          updated_at?: string
        }
      }
      rooms: {
        Row: {
          id: string
          name: string
          type: string
          capacity: number
          price_per_night: number
          description: string
          amenities: string[]
          image_url: string
          status: 'available' | 'occupied' | 'maintenance'
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          name: string
          type: string
          capacity: number
          price_per_night: number
          description: string
          amenities?: string[]
          image_url?: string
          status?: 'available' | 'occupied' | 'maintenance'
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          name?: string
          type?: string
          capacity?: number
          price_per_night?: number
          description?: string
          amenities?: string[]
          image_url?: string
          status?: 'available' | 'occupied' | 'maintenance'
          created_at?: string
          updated_at?: string
        }
      }
      bookings: {
        Row: {
          id: string
          user_id: string
          room_id: string
          check_in: string
          check_out: string
          guests: number
          total_price: number
          status: 'pending' | 'confirmed' | 'cancelled' | 'completed'
          special_requests: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          room_id: string
          check_in: string
          check_out: string
          guests: number
          total_price: number
          status?: 'pending' | 'confirmed' | 'cancelled' | 'completed'
          special_requests?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          room_id?: string
          check_in?: string
          check_out?: string
          guests?: number
          total_price?: number
          status?: 'pending' | 'confirmed' | 'cancelled' | 'completed'
          special_requests?: string | null
          created_at?: string
          updated_at?: string
        }
      }
      payments: {
        Row: {
          id: string
          booking_id: string
          amount: number
          payment_method: string
          status: 'pending' | 'completed' | 'failed' | 'refunded'
          transaction_id: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          booking_id: string
          amount: number
          payment_method: string
          status?: 'pending' | 'completed' | 'failed' | 'refunded'
          transaction_id?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          booking_id?: string
          amount?: number
          payment_method?: string
          status?: 'pending' | 'completed' | 'failed' | 'refunded'
          transaction_id?: string | null
          created_at?: string
          updated_at?: string
        }
      }
    }
  }
}
