export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "12.2.3 (519615d)"
  }
  public: {
    Tables: {
      document_access: {
        Row: {
          access_level: string
          document_id: string | null
          expires_at: string | null
          firm_id: string | null
          granted_at: string | null
          granted_by: string | null
          id: string
          user_id: string | null
        }
        Insert: {
          access_level: string
          document_id?: string | null
          expires_at?: string | null
          firm_id?: string | null
          granted_at?: string | null
          granted_by?: string | null
          id?: string
          user_id?: string | null
        }
        Update: {
          access_level?: string
          document_id?: string | null
          expires_at?: string | null
          firm_id?: string | null
          granted_at?: string | null
          granted_by?: string | null
          id?: string
          user_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "document_access_document_id_fkey"
            columns: ["document_id"]
            isOneToOne: false
            referencedRelation: "documents"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "document_access_firm_id_fkey"
            columns: ["firm_id"]
            isOneToOne: false
            referencedRelation: "firms"
            referencedColumns: ["id"]
          },
        ]
      }
      document_chunks: {
        Row: {
          chunk_index: number
          content: string
          content_hash: string
          created_at: string | null
          document_id: string
          embedding: string | null
          id: string
          processing_file_id: string | null
          content: string | null
          token_count: number | null
        }
        Insert: {
          chunk_index: number
          content: string
          content_hash: string
          created_at?: string | null
          document_id: string
          embedding?: string | null
          id?: string
          processing_file_id?: string | null
          content?: string | null
          token_count?: number | null
        }
        Update: {
          chunk_index?: number
          content?: string
          content_hash?: string
          created_at?: string | null
          document_id?: string
          embedding?: string | null
          id?: string
          processing_file_id?: string | null
          content?: string | null
          token_count?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "document_chunks_document_id_fkey"
            columns: ["document_id"]
            isOneToOne: false
            referencedRelation: "documents"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "fk_document_chunks_processing_file"
            columns: ["processing_file_id"]
            isOneToOne: false
            referencedRelation: "processing_files"
            referencedColumns: ["id"]
          },
        ]
      }
      document_collection_items: {
        Row: {
          added_at: string | null
          added_by: string | null
          collection_id: string
          document_id: string
          notes: string | null
          position: number | null
        }
        Insert: {
          added_at?: string | null
          added_by?: string | null
          collection_id: string
          document_id: string
          notes?: string | null
          position?: number | null
        }
        Update: {
          added_at?: string | null
          added_by?: string | null
          collection_id?: string
          document_id?: string
          notes?: string | null
          position?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "document_collection_items_collection_id_fkey"
            columns: ["collection_id"]
            isOneToOne: false
            referencedRelation: "document_collections"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "document_collection_items_document_id_fkey"
            columns: ["document_id"]
            isOneToOne: false
            referencedRelation: "documents"
            referencedColumns: ["id"]
          },
        ]
      }
      document_collections: {
        Row: {
          created_at: string | null
          created_by: string | null
          description: string | null
          firm_id: string | null
          id: string
          name: string
          parent_id: string | null
          updated_at: string | null
        }
        Insert: {
          created_at?: string | null
          created_by?: string | null
          description?: string | null
          firm_id?: string | null
          id?: string
          name: string
          parent_id?: string | null
          updated_at?: string | null
        }
        Update: {
          created_at?: string | null
          created_by?: string | null
          description?: string | null
          firm_id?: string | null
          id?: string
          name?: string
          parent_id?: string | null
          updated_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "document_collections_firm_id_fkey"
            columns: ["firm_id"]
            isOneToOne: false
            referencedRelation: "firms"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "document_collections_parent_id_fkey"
            columns: ["parent_id"]
            isOneToOne: false
            referencedRelation: "document_collections"
            referencedColumns: ["id"]
          },
        ]
      }
      document_relationships: {
        Row: {
          created_at: string | null
          created_by: string | null
          id: string
          metadata: Json | null
          relationship_type: string
          source_document_id: string | null
          target_document_id: string | null
        }
        Insert: {
          created_at?: string | null
          created_by?: string | null
          id?: string
          metadata?: Json | null
          relationship_type: string
          source_document_id?: string | null
          target_document_id?: string | null
        }
        Update: {
          created_at?: string | null
          created_by?: string | null
          id?: string
          metadata?: Json | null
          relationship_type?: string
          source_document_id?: string | null
          target_document_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "document_relationships_source_document_id_fkey"
            columns: ["source_document_id"]
            isOneToOne: false
            referencedRelation: "documents"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "document_relationships_target_document_id_fkey"
            columns: ["target_document_id"]
            isOneToOne: false
            referencedRelation: "documents"
            referencedColumns: ["id"]
          },
        ]
      }
      document_versions: {
        Row: {
          change_summary: string | null
          content_hash: string
          created_at: string | null
          created_by: string | null
          document_id: string | null
          file_size: number | null
          id: string
          is_current: boolean | null
          storage_path: string | null
          version_number: number
        }
        Insert: {
          change_summary?: string | null
          content_hash: string
          created_at?: string | null
          created_by?: string | null
          document_id?: string | null
          file_size?: number | null
          id?: string
          is_current?: boolean | null
          storage_path?: string | null
          version_number: number
        }
        Update: {
          change_summary?: string | null
          content_hash?: string
          created_at?: string | null
          created_by?: string | null
          document_id?: string | null
          file_size?: number | null
          id?: string
          is_current?: boolean | null
          storage_path?: string | null
          version_number?: number
        }
        Relationships: [
          {
            foreignKeyName: "document_versions_document_id_fkey"
            columns: ["document_id"]
            isOneToOne: false
            referencedRelation: "documents"
            referencedColumns: ["id"]
          },
        ]
      }
      documents: {
        Row: {
          archived_at: string | null
          authors: Json | null
          case_name: string | null
          case_number: string | null
          char_count: number | null
          chunk_count: number | null
          citation: string | null
          confidence_score: number | null
          content_hash: string | null
          court: string | null
          created_at: string | null
          damage_amounts: Json | null
          date: string | null
          deleted_at: string | null
          deleted_by: string | null
          description: string | null
          discount_rates: Json | null
          doc_category: string | null
          doc_type: string
          education_levels: Json | null
          file_size: number | null
          filename: string
          id: string
          is_archived: boolean | null
          is_deleted: boolean | null
          is_reviewed: boolean | null
          jurisdiction: string | null
          keywords: Json | null
          methodologies: Json | null
          mime_type: string | null
          notes: string | null
          original_filename: string | null
          page_count: number | null
          practice_area: string | null
          review_notes: string | null
          reviewed_at: string | null
          reviewed_by: string | null
          status: string | null
          storage_bucket: string | null
          storage_path: string | null
          subject_ages: Json | null
          summary: string | null
          tags: Json | null
          title: string | null
          updated_at: string | null
          uploaded_by: string | null
          word_count: number | null
        }
        Insert: {
          archived_at?: string | null
          authors?: Json | null
          case_name?: string | null
          case_number?: string | null
          char_count?: number | null
          chunk_count?: number | null
          citation?: string | null
          confidence_score?: number | null
          content_hash?: string | null
          court?: string | null
          created_at?: string | null
          damage_amounts?: Json | null
          date?: string | null
          deleted_at?: string | null
          deleted_by?: string | null
          description?: string | null
          discount_rates?: Json | null
          doc_category?: string | null
          doc_type?: string
          education_levels?: Json | null
          file_size?: number | null
          filename: string
          id?: string
          is_archived?: boolean | null
          is_deleted?: boolean | null
          is_reviewed?: boolean | null
          jurisdiction?: string | null
          keywords?: Json | null
          methodologies?: Json | null
          mime_type?: string | null
          notes?: string | null
          original_filename?: string | null
          page_count?: number | null
          practice_area?: string | null
          review_notes?: string | null
          reviewed_at?: string | null
          reviewed_by?: string | null
          status?: string | null
          storage_bucket?: string | null
          storage_path?: string | null
          subject_ages?: Json | null
          summary?: string | null
          tags?: Json | null
          title?: string | null
          updated_at?: string | null
          uploaded_by?: string | null
          word_count?: number | null
        }
        Update: {
          archived_at?: string | null
          authors?: Json | null
          case_name?: string | null
          case_number?: string | null
          char_count?: number | null
          chunk_count?: number | null
          citation?: string | null
          confidence_score?: number | null
          content_hash?: string | null
          court?: string | null
          created_at?: string | null
          damage_amounts?: Json | null
          date?: string | null
          deleted_at?: string | null
          deleted_by?: string | null
          description?: string | null
          discount_rates?: Json | null
          doc_category?: string | null
          doc_type?: string
          education_levels?: Json | null
          file_size?: number | null
          filename?: string
          id?: string
          is_archived?: boolean | null
          is_deleted?: boolean | null
          is_reviewed?: boolean | null
          jurisdiction?: string | null
          keywords?: Json | null
          methodologies?: Json | null
          mime_type?: string | null
          notes?: string | null
          original_filename?: string | null
          page_count?: number | null
          practice_area?: string | null
          review_notes?: string | null
          reviewed_at?: string | null
          reviewed_by?: string | null
          status?: string | null
          storage_bucket?: string | null
          storage_path?: string | null
          subject_ages?: Json | null
          summary?: string | null
          tags?: Json | null
          title?: string | null
          updated_at?: string | null
          uploaded_by?: string | null
          word_count?: number | null
        }
        Relationships: []
      }
      firms: {
        Row: {
          address_1: string | null
          address_2: string | null
          city: string | null
          created_at: string | null
          domain: string
          firm_admin_id: string | null
          id: string
          image_url: string | null
          main_phone: string | null
          name: string
          slug: string | null
          state: string | null
          updated_at: string | null
          zip_code: string | null
        }
        Insert: {
          address_1?: string | null
          address_2?: string | null
          city?: string | null
          created_at?: string | null
          domain: string
          firm_admin_id?: string | null
          id?: string
          image_url?: string | null
          main_phone?: string | null
          name: string
          slug?: string | null
          state?: string | null
          updated_at?: string | null
          zip_code?: string | null
        }
        Update: {
          address_1?: string | null
          address_2?: string | null
          city?: string | null
          created_at?: string | null
          domain?: string
          firm_admin_id?: string | null
          id?: string
          image_url?: string | null
          main_phone?: string | null
          name?: string
          slug?: string | null
          state?: string | null
          updated_at?: string | null
          zip_code?: string | null
        }
        Relationships: []
      }
      forensic_documents: {
        Row: {
          chapter_section: string | null
          created_at: string | null
          id: string
          source_name: string
          source_type: string
        }
        Insert: {
          chapter_section?: string | null
          created_at?: string | null
          id?: string
          source_name: string
          source_type: string
        }
        Update: {
          chapter_section?: string | null
          created_at?: string | null
          id?: string
          source_name?: string
          source_type?: string
        }
        Relationships: []
      }
      form_audit_trail: {
        Row: {
          action_type: string
          created_at: string
          firm_id: string | null
          form_id: string
          form_type: string
          id: string
          metadata: Json | null
          submitted_by: string
        }
        Insert: {
          action_type: string
          created_at?: string
          firm_id?: string | null
          form_id: string
          form_type: string
          id?: string
          metadata?: Json | null
          submitted_by: string
        }
        Update: {
          action_type?: string
          created_at?: string
          firm_id?: string | null
          form_id?: string
          form_type?: string
          id?: string
          metadata?: Json | null
          submitted_by?: string
        }
        Relationships: [
          {
            foreignKeyName: "form_audit_trail_firm_id_fkey"
            columns: ["firm_id"]
            isOneToOne: false
            referencedRelation: "firms"
            referencedColumns: ["id"]
          },
        ]
      }
      personal_injury_drafts: {
        Row: {
          additional_info: string | null
          address1: string | null
          address2: string | null
          caregiver_claim: string | null
          city: string | null
          created_at: string
          date_of_birth: string | null
          defendant: string | null
          dependent_care: string | null
          disability_rating: string | null
          education_plans: string | null
          email: string | null
          errands: string | null
          ethnicity: string | null
          firm_id: string | null
          first_name: string | null
          future_medical: string | null
          gender: string | null
          home_maintenance: string | null
          household_members: Json | null
          id: string
          incident_date: string | null
          indoor_housework: string | null
          injury_description: string | null
          last_name: string | null
          life_expectancy: string | null
          marital_status: string | null
          matter_no: string | null
          meal_prep: string | null
          opposing_counsel_firm: string | null
          opposing_economist: string | null
          parent_education: string | null
          pet_care: string | null
          phone: string | null
          phone_type: string | null
          post_injury_advancements: string | null
          post_injury_bonus: string | null
          post_injury_duties: string | null
          post_injury_education: string | null
          post_injury_employer: string | null
          post_injury_employment_status: string | null
          post_injury_family_health: string | null
          post_injury_individual_health: string | null
          post_injury_investment_plan: string | null
          post_injury_job_expenses: string | null
          post_injury_job_title: string | null
          post_injury_life_insurance: string | null
          post_injury_other_benefits: string | null
          post_injury_overtime: string | null
          post_injury_retirement_age: string | null
          post_injury_retirement_plan: string | null
          post_injury_salary: string | null
          post_injury_start_date: string | null
          post_injury_stock_options: string | null
          post_injury_work_steady: string | null
          post_injury_years: Json | null
          pre_injury_advancements: string | null
          pre_injury_bonus: string | null
          pre_injury_career_trajectory: string | null
          pre_injury_duties: string | null
          pre_injury_education: string | null
          pre_injury_employer: string | null
          pre_injury_employment_status: string | null
          pre_injury_family_health: string | null
          pre_injury_individual_health: string | null
          pre_injury_investment_plan: string | null
          pre_injury_job_expenses: string | null
          pre_injury_job_title: string | null
          pre_injury_life_insurance: string | null
          pre_injury_other_benefits: string | null
          pre_injury_overtime: string | null
          pre_injury_retirement_age: string | null
          pre_injury_retirement_plan: string | null
          pre_injury_salary: string | null
          pre_injury_skills: string | null
          pre_injury_start_date: string | null
          pre_injury_stock_options: string | null
          pre_injury_work_steady: string | null
          pre_injury_years: Json | null
          settlement_date: string | null
          state: string | null
          status: string
          submitted_by: string
          trial_date: string | null
          trial_location: string | null
          updated_at: string
          uploaded_files: Json | null
          vehicle_maintenance: string | null
          zip_code: string | null
        }
        Insert: {
          additional_info?: string | null
          address1?: string | null
          address2?: string | null
          caregiver_claim?: string | null
          city?: string | null
          created_at?: string
          date_of_birth?: string | null
          defendant?: string | null
          dependent_care?: string | null
          disability_rating?: string | null
          education_plans?: string | null
          email?: string | null
          errands?: string | null
          ethnicity?: string | null
          firm_id?: string | null
          first_name?: string | null
          future_medical?: string | null
          gender?: string | null
          home_maintenance?: string | null
          household_members?: Json | null
          id?: string
          incident_date?: string | null
          indoor_housework?: string | null
          injury_description?: string | null
          last_name?: string | null
          life_expectancy?: string | null
          marital_status?: string | null
          matter_no?: string | null
          meal_prep?: string | null
          opposing_counsel_firm?: string | null
          opposing_economist?: string | null
          parent_education?: string | null
          pet_care?: string | null
          phone?: string | null
          phone_type?: string | null
          post_injury_advancements?: string | null
          post_injury_bonus?: string | null
          post_injury_duties?: string | null
          post_injury_education?: string | null
          post_injury_employer?: string | null
          post_injury_employment_status?: string | null
          post_injury_family_health?: string | null
          post_injury_individual_health?: string | null
          post_injury_investment_plan?: string | null
          post_injury_job_expenses?: string | null
          post_injury_job_title?: string | null
          post_injury_life_insurance?: string | null
          post_injury_other_benefits?: string | null
          post_injury_overtime?: string | null
          post_injury_retirement_age?: string | null
          post_injury_retirement_plan?: string | null
          post_injury_salary?: string | null
          post_injury_start_date?: string | null
          post_injury_stock_options?: string | null
          post_injury_work_steady?: string | null
          post_injury_years?: Json | null
          pre_injury_advancements?: string | null
          pre_injury_bonus?: string | null
          pre_injury_career_trajectory?: string | null
          pre_injury_duties?: string | null
          pre_injury_education?: string | null
          pre_injury_employer?: string | null
          pre_injury_employment_status?: string | null
          pre_injury_family_health?: string | null
          pre_injury_individual_health?: string | null
          pre_injury_investment_plan?: string | null
          pre_injury_job_expenses?: string | null
          pre_injury_job_title?: string | null
          pre_injury_life_insurance?: string | null
          pre_injury_other_benefits?: string | null
          pre_injury_overtime?: string | null
          pre_injury_retirement_age?: string | null
          pre_injury_retirement_plan?: string | null
          pre_injury_salary?: string | null
          pre_injury_skills?: string | null
          pre_injury_start_date?: string | null
          pre_injury_stock_options?: string | null
          pre_injury_work_steady?: string | null
          pre_injury_years?: Json | null
          settlement_date?: string | null
          state?: string | null
          status?: string
          submitted_by: string
          trial_date?: string | null
          trial_location?: string | null
          updated_at?: string
          uploaded_files?: Json | null
          vehicle_maintenance?: string | null
          zip_code?: string | null
        }
        Update: {
          additional_info?: string | null
          address1?: string | null
          address2?: string | null
          caregiver_claim?: string | null
          city?: string | null
          created_at?: string
          date_of_birth?: string | null
          defendant?: string | null
          dependent_care?: string | null
          disability_rating?: string | null
          education_plans?: string | null
          email?: string | null
          errands?: string | null
          ethnicity?: string | null
          firm_id?: string | null
          first_name?: string | null
          future_medical?: string | null
          gender?: string | null
          home_maintenance?: string | null
          household_members?: Json | null
          id?: string
          incident_date?: string | null
          indoor_housework?: string | null
          injury_description?: string | null
          last_name?: string | null
          life_expectancy?: string | null
          marital_status?: string | null
          matter_no?: string | null
          meal_prep?: string | null
          opposing_counsel_firm?: string | null
          opposing_economist?: string | null
          parent_education?: string | null
          pet_care?: string | null
          phone?: string | null
          phone_type?: string | null
          post_injury_advancements?: string | null
          post_injury_bonus?: string | null
          post_injury_duties?: string | null
          post_injury_education?: string | null
          post_injury_employer?: string | null
          post_injury_employment_status?: string | null
          post_injury_family_health?: string | null
          post_injury_individual_health?: string | null
          post_injury_investment_plan?: string | null
          post_injury_job_expenses?: string | null
          post_injury_job_title?: string | null
          post_injury_life_insurance?: string | null
          post_injury_other_benefits?: string | null
          post_injury_overtime?: string | null
          post_injury_retirement_age?: string | null
          post_injury_retirement_plan?: string | null
          post_injury_salary?: string | null
          post_injury_start_date?: string | null
          post_injury_stock_options?: string | null
          post_injury_work_steady?: string | null
          post_injury_years?: Json | null
          pre_injury_advancements?: string | null
          pre_injury_bonus?: string | null
          pre_injury_career_trajectory?: string | null
          pre_injury_duties?: string | null
          pre_injury_education?: string | null
          pre_injury_employer?: string | null
          pre_injury_employment_status?: string | null
          pre_injury_family_health?: string | null
          pre_injury_individual_health?: string | null
          pre_injury_investment_plan?: string | null
          pre_injury_job_expenses?: string | null
          pre_injury_job_title?: string | null
          pre_injury_life_insurance?: string | null
          pre_injury_other_benefits?: string | null
          pre_injury_overtime?: string | null
          pre_injury_retirement_age?: string | null
          pre_injury_retirement_plan?: string | null
          pre_injury_salary?: string | null
          pre_injury_skills?: string | null
          pre_injury_start_date?: string | null
          pre_injury_stock_options?: string | null
          pre_injury_work_steady?: string | null
          pre_injury_years?: Json | null
          settlement_date?: string | null
          state?: string | null
          status?: string
          submitted_by?: string
          trial_date?: string | null
          trial_location?: string | null
          updated_at?: string
          uploaded_files?: Json | null
          vehicle_maintenance?: string | null
          zip_code?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "personal_injury_drafts_normalized_firm_id_fkey"
            columns: ["firm_id"]
            isOneToOne: false
            referencedRelation: "firms"
            referencedColumns: ["id"]
          },
        ]
      }
      personal_injury_forms: {
        Row: {
          additional_info: string
          address1: string
          address2: string | null
          caregiver_claim: string
          city: string
          created_at: string
          date_of_birth: string
          defendant: string | null
          dependent_care: string
          disability_rating: string
          education_plans: string
          email: string
          errands: string
          ethnicity: string
          firm_id: string | null
          first_name: string
          future_medical: string
          gender: string
          home_maintenance: string
          household_members: Json | null
          id: string
          incident_date: string
          indoor_housework: string
          injury_description: string
          last_name: string
          life_expectancy: string
          marital_status: string
          matter_no: string | null
          meal_prep: string
          opposing_counsel_firm: string
          opposing_economist: string
          parent_education: string
          pet_care: string
          phone: string
          phone_type: string
          post_injury_advancements: string
          post_injury_bonus: string | null
          post_injury_duties: string
          post_injury_education: string
          post_injury_employer: string
          post_injury_employment_status: string
          post_injury_family_health: string | null
          post_injury_individual_health: string | null
          post_injury_investment_plan: string | null
          post_injury_job_expenses: string
          post_injury_job_title: string
          post_injury_life_insurance: string | null
          post_injury_other_benefits: string | null
          post_injury_overtime: string
          post_injury_retirement_age: string
          post_injury_retirement_plan: string | null
          post_injury_salary: string
          post_injury_start_date: string
          post_injury_stock_options: string | null
          post_injury_work_steady: string
          post_injury_years: Json | null
          pre_injury_advancements: string
          pre_injury_bonus: string | null
          pre_injury_career_trajectory: string
          pre_injury_duties: string
          pre_injury_education: string
          pre_injury_employer: string
          pre_injury_employment_status: string
          pre_injury_family_health: string | null
          pre_injury_individual_health: string | null
          pre_injury_investment_plan: string | null
          pre_injury_job_expenses: string
          pre_injury_job_title: string
          pre_injury_life_insurance: string | null
          pre_injury_other_benefits: string | null
          pre_injury_overtime: string
          pre_injury_retirement_age: string
          pre_injury_retirement_plan: string | null
          pre_injury_salary: string
          pre_injury_skills: string
          pre_injury_start_date: string
          pre_injury_stock_options: string | null
          pre_injury_work_steady: string
          pre_injury_years: Json | null
          settlement_date: string
          state: string
          status: string
          submitted_by: string
          trial_date: string
          trial_location: string
          updated_at: string
          uploaded_files: Json | null
          vehicle_maintenance: string
          version: number | null
          version_history: Json | null
          zip_code: string
        }
        Insert: {
          additional_info: string
          address1: string
          address2?: string | null
          caregiver_claim: string
          city: string
          created_at?: string
          date_of_birth: string
          defendant?: string | null
          dependent_care: string
          disability_rating: string
          education_plans: string
          email: string
          errands: string
          ethnicity: string
          firm_id?: string | null
          first_name: string
          future_medical: string
          gender: string
          home_maintenance: string
          household_members?: Json | null
          id?: string
          incident_date: string
          indoor_housework: string
          injury_description: string
          last_name: string
          life_expectancy: string
          marital_status: string
          matter_no?: string | null
          meal_prep: string
          opposing_counsel_firm: string
          opposing_economist: string
          parent_education: string
          pet_care: string
          phone: string
          phone_type: string
          post_injury_advancements: string
          post_injury_bonus?: string | null
          post_injury_duties: string
          post_injury_education: string
          post_injury_employer: string
          post_injury_employment_status: string
          post_injury_family_health?: string | null
          post_injury_individual_health?: string | null
          post_injury_investment_plan?: string | null
          post_injury_job_expenses: string
          post_injury_job_title: string
          post_injury_life_insurance?: string | null
          post_injury_other_benefits?: string | null
          post_injury_overtime: string
          post_injury_retirement_age: string
          post_injury_retirement_plan?: string | null
          post_injury_salary: string
          post_injury_start_date: string
          post_injury_stock_options?: string | null
          post_injury_work_steady: string
          post_injury_years?: Json | null
          pre_injury_advancements: string
          pre_injury_bonus?: string | null
          pre_injury_career_trajectory: string
          pre_injury_duties: string
          pre_injury_education: string
          pre_injury_employer: string
          pre_injury_employment_status: string
          pre_injury_family_health?: string | null
          pre_injury_individual_health?: string | null
          pre_injury_investment_plan?: string | null
          pre_injury_job_expenses: string
          pre_injury_job_title: string
          pre_injury_life_insurance?: string | null
          pre_injury_other_benefits?: string | null
          pre_injury_overtime: string
          pre_injury_retirement_age: string
          pre_injury_retirement_plan?: string | null
          pre_injury_salary: string
          pre_injury_skills: string
          pre_injury_start_date: string
          pre_injury_stock_options?: string | null
          pre_injury_work_steady: string
          pre_injury_years?: Json | null
          settlement_date: string
          state: string
          status?: string
          submitted_by: string
          trial_date: string
          trial_location: string
          updated_at?: string
          uploaded_files?: Json | null
          vehicle_maintenance: string
          version?: number | null
          version_history?: Json | null
          zip_code: string
        }
        Update: {
          additional_info?: string
          address1?: string
          address2?: string | null
          caregiver_claim?: string
          city?: string
          created_at?: string
          date_of_birth?: string
          defendant?: string | null
          dependent_care?: string
          disability_rating?: string
          education_plans?: string
          email?: string
          errands?: string
          ethnicity?: string
          firm_id?: string | null
          first_name?: string
          future_medical?: string
          gender?: string
          home_maintenance?: string
          household_members?: Json | null
          id?: string
          incident_date?: string
          indoor_housework?: string
          injury_description?: string
          last_name?: string
          life_expectancy?: string
          marital_status?: string
          matter_no?: string | null
          meal_prep?: string
          opposing_counsel_firm?: string
          opposing_economist?: string
          parent_education?: string
          pet_care?: string
          phone?: string
          phone_type?: string
          post_injury_advancements?: string
          post_injury_bonus?: string | null
          post_injury_duties?: string
          post_injury_education?: string
          post_injury_employer?: string
          post_injury_employment_status?: string
          post_injury_family_health?: string | null
          post_injury_individual_health?: string | null
          post_injury_investment_plan?: string | null
          post_injury_job_expenses?: string
          post_injury_job_title?: string
          post_injury_life_insurance?: string | null
          post_injury_other_benefits?: string | null
          post_injury_overtime?: string
          post_injury_retirement_age?: string
          post_injury_retirement_plan?: string | null
          post_injury_salary?: string
          post_injury_start_date?: string
          post_injury_stock_options?: string | null
          post_injury_work_steady?: string
          post_injury_years?: Json | null
          pre_injury_advancements?: string
          pre_injury_bonus?: string | null
          pre_injury_career_trajectory?: string
          pre_injury_duties?: string
          pre_injury_education?: string
          pre_injury_employer?: string
          pre_injury_employment_status?: string
          pre_injury_family_health?: string | null
          pre_injury_individual_health?: string | null
          pre_injury_investment_plan?: string | null
          pre_injury_job_expenses?: string
          pre_injury_job_title?: string
          pre_injury_life_insurance?: string | null
          pre_injury_other_benefits?: string | null
          pre_injury_overtime?: string
          pre_injury_retirement_age?: string
          pre_injury_retirement_plan?: string | null
          pre_injury_salary?: string
          pre_injury_skills?: string
          pre_injury_start_date?: string
          pre_injury_stock_options?: string | null
          pre_injury_work_steady?: string
          pre_injury_years?: Json | null
          settlement_date?: string
          state?: string
          status?: string
          submitted_by?: string
          trial_date?: string
          trial_location?: string
          updated_at?: string
          uploaded_files?: Json | null
          vehicle_maintenance?: string
          version?: number | null
          version_history?: Json | null
          zip_code?: string
        }
        Relationships: [
          {
            foreignKeyName: "personal_injury_forms_normalized_firm_id_fkey"
            columns: ["firm_id"]
            isOneToOne: false
            referencedRelation: "firms"
            referencedColumns: ["id"]
          },
        ]
      }
      processing_files: {
        Row: {
          ai_authors: Json | null
          ai_bluebook_citation: string | null
          ai_confidence_scores: Json | null
          ai_description: string | null
          ai_doc_category: string | null
          ai_doc_type: string | null
          ai_keywords: Json | null
          ai_publication_date: string | null
          ai_title: string | null
          batch_id: string
          content_hash: string | null
          created_at: string | null
          document_id: string | null
          error_message: string | null
          extracted_metadata: Json | null
          file_size: number
          id: string
          last_retry_at: string | null
          mime_type: string
          original_filename: string
          priority: number | null
          retry_count: number | null
          review_notes: string | null
          reviewed_at: string | null
          reviewed_by: string | null
          status: string
          stored_path: string
          updated_at: string | null
          user_metadata: Json | null
        }
        Insert: {
          ai_authors?: Json | null
          ai_bluebook_citation?: string | null
          ai_confidence_scores?: Json | null
          ai_description?: string | null
          ai_doc_category?: string | null
          ai_doc_type?: string | null
          ai_keywords?: Json | null
          ai_publication_date?: string | null
          ai_title?: string | null
          batch_id: string
          content_hash?: string | null
          created_at?: string | null
          document_id?: string | null
          error_message?: string | null
          extracted_metadata?: Json | null
          file_size: number
          id?: string
          last_retry_at?: string | null
          mime_type: string
          original_filename: string
          priority?: number | null
          retry_count?: number | null
          review_notes?: string | null
          reviewed_at?: string | null
          reviewed_by?: string | null
          status?: string
          stored_path: string
          updated_at?: string | null
          user_metadata?: Json | null
        }
        Update: {
          ai_authors?: Json | null
          ai_bluebook_citation?: string | null
          ai_confidence_scores?: Json | null
          ai_description?: string | null
          ai_doc_category?: string | null
          ai_doc_type?: string | null
          ai_keywords?: Json | null
          ai_publication_date?: string | null
          ai_title?: string | null
          batch_id?: string
          content_hash?: string | null
          created_at?: string | null
          document_id?: string | null
          error_message?: string | null
          extracted_metadata?: Json | null
          file_size?: number
          id?: string
          last_retry_at?: string | null
          mime_type?: string
          original_filename?: string
          priority?: number | null
          retry_count?: number | null
          review_notes?: string | null
          reviewed_at?: string | null
          reviewed_by?: string | null
          status?: string
          stored_path?: string
          updated_at?: string | null
          user_metadata?: Json | null
        }
        Relationships: [
          {
            foreignKeyName: "fk_processing_files_document"
            columns: ["document_id"]
            isOneToOne: false
            referencedRelation: "documents"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "processing_files_document_id_fkey"
            columns: ["document_id"]
            isOneToOne: false
            referencedRelation: "documents"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "processing_files_job_id_fkey"
            columns: ["batch_id"]
            isOneToOne: false
            referencedRelation: "processing_jobs"
            referencedColumns: ["id"]
          },
        ]
      }
      processing_jobs: {
        Row: {
          completed_files: number | null
          created_at: string | null
          error_message: string | null
          failed_files: number | null
          id: string
          processed_files: number | null
          status: string
          total_files: number
          updated_at: string | null
        }
        Insert: {
          completed_files?: number | null
          created_at?: string | null
          error_message?: string | null
          failed_files?: number | null
          id?: string
          processed_files?: number | null
          status?: string
          total_files: number
          updated_at?: string | null
        }
        Update: {
          completed_files?: number | null
          created_at?: string | null
          error_message?: string | null
          failed_files?: number | null
          id?: string
          processed_files?: number | null
          status?: string
          total_files?: number
          updated_at?: string | null
        }
        Relationships: []
      }
      processing_webhooks: {
        Row: {
          batch_id: string | null
          created_at: string | null
          events: string[]
          id: string
          last_triggered_at: string | null
          trigger_count: number | null
          webhook_url: string
        }
        Insert: {
          batch_id?: string | null
          created_at?: string | null
          events: string[]
          id?: string
          last_triggered_at?: string | null
          trigger_count?: number | null
          webhook_url: string
        }
        Update: {
          batch_id?: string | null
          created_at?: string | null
          events?: string[]
          id?: string
          last_triggered_at?: string | null
          trigger_count?: number | null
          webhook_url?: string
        }
        Relationships: [
          {
            foreignKeyName: "processing_webhooks_job_id_fkey"
            columns: ["batch_id"]
            isOneToOne: false
            referencedRelation: "processing_jobs"
            referencedColumns: ["id"]
          },
        ]
      }
      rag_admins: {
        Row: {
          created_at: string | null
          created_by: string | null
          email: string
          id: string
          is_active: boolean | null
        }
        Insert: {
          created_at?: string | null
          created_by?: string | null
          email: string
          id?: string
          is_active?: boolean | null
        }
        Update: {
          created_at?: string | null
          created_by?: string | null
          email?: string
          id?: string
          is_active?: boolean | null
        }
        Relationships: []
      }
      saved_searches: {
        Row: {
          created_at: string | null
          description: string | null
          filters: Json | null
          firm_id: string | null
          id: string
          is_shared: boolean | null
          last_used_at: string | null
          name: string
          query_text: string | null
          updated_at: string | null
          user_id: string | null
        }
        Insert: {
          created_at?: string | null
          description?: string | null
          filters?: Json | null
          firm_id?: string | null
          id?: string
          is_shared?: boolean | null
          last_used_at?: string | null
          name: string
          query_text?: string | null
          updated_at?: string | null
          user_id?: string | null
        }
        Update: {
          created_at?: string | null
          description?: string | null
          filters?: Json | null
          firm_id?: string | null
          id?: string
          is_shared?: boolean | null
          last_used_at?: string | null
          name?: string
          query_text?: string | null
          updated_at?: string | null
          user_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "saved_searches_firm_id_fkey"
            columns: ["firm_id"]
            isOneToOne: false
            referencedRelation: "firms"
            referencedColumns: ["id"]
          },
        ]
      }
      search_feedback: {
        Row: {
          created_at: string | null
          document_id: string | null
          feedback_type: string | null
          id: string
          search_log_id: string | null
          user_id: string | null
        }
        Insert: {
          created_at?: string | null
          document_id?: string | null
          feedback_type?: string | null
          id?: string
          search_log_id?: string | null
          user_id?: string | null
        }
        Update: {
          created_at?: string | null
          document_id?: string | null
          feedback_type?: string | null
          id?: string
          search_log_id?: string | null
          user_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "search_feedback_document_id_fkey"
            columns: ["document_id"]
            isOneToOne: false
            referencedRelation: "documents"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "search_feedback_search_log_id_fkey"
            columns: ["search_log_id"]
            isOneToOne: false
            referencedRelation: "search_logs"
            referencedColumns: ["id"]
          },
        ]
      }
      search_logs: {
        Row: {
          created_at: string | null
          doc_type_filter: string | null
          id: string
          jurisdiction_filter: string | null
          practice_area_filter: string | null
          query_text: string | null
          results_count: number | null
          session_id: string | null
          user_id: string | null
        }
        Insert: {
          created_at?: string | null
          doc_type_filter?: string | null
          id?: string
          jurisdiction_filter?: string | null
          practice_area_filter?: string | null
          query_text?: string | null
          results_count?: number | null
          session_id?: string | null
          user_id?: string | null
        }
        Update: {
          created_at?: string | null
          doc_type_filter?: string | null
          id?: string
          jurisdiction_filter?: string | null
          practice_area_filter?: string | null
          query_text?: string | null
          results_count?: number | null
          session_id?: string | null
          user_id?: string | null
        }
        Relationships: []
      }
      user_invitations: {
        Row: {
          accepted_at: string | null
          email: string
          firm_id: string | null
          id: string
          invited_at: string | null
          invited_by: string | null
          role: string
        }
        Insert: {
          accepted_at?: string | null
          email: string
          firm_id?: string | null
          id?: string
          invited_at?: string | null
          invited_by?: string | null
          role: string
        }
        Update: {
          accepted_at?: string | null
          email?: string
          firm_id?: string | null
          id?: string
          invited_at?: string | null
          invited_by?: string | null
          role?: string
        }
        Relationships: [
          {
            foreignKeyName: "user_invitations_firm_id_fkey"
            columns: ["firm_id"]
            isOneToOne: false
            referencedRelation: "firms"
            referencedColumns: ["id"]
          },
        ]
      }
      user_profiles: {
        Row: {
          created_at: string | null
          firm_id: string | null
          first_name: string | null
          id: string
          last_name: string | null
          role: string
          updated_at: string | null
          user_id: string | null
        }
        Insert: {
          created_at?: string | null
          firm_id?: string | null
          first_name?: string | null
          id?: string
          last_name?: string | null
          role: string
          updated_at?: string | null
          user_id?: string | null
        }
        Update: {
          created_at?: string | null
          firm_id?: string | null
          first_name?: string | null
          id?: string
          last_name?: string | null
          role?: string
          updated_at?: string | null
          user_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "user_profiles_firm_id_fkey"
            columns: ["firm_id"]
            isOneToOne: false
            referencedRelation: "firms"
            referencedColumns: ["id"]
          },
        ]
      }
      wrongful_death_drafts: {
        Row: {
          additional_info: string | null
          address1: string | null
          address2: string | null
          advancements: string | null
          bonus: string | null
          career_trajectory: string | null
          city: string | null
          created_at: string
          date_of_birth: string | null
          date_of_death: string | null
          defendant: string | null
          dependent_care: string | null
          education_level: string | null
          employer_name: string | null
          employment_status: string | null
          employment_years: Json | null
          errands: string | null
          ethnicity: string | null
          family_health: string | null
          firm_id: string | null
          first_name: string | null
          gender: string | null
          health_issues: string | null
          home_maintenance: string | null
          household_dependents: Json | null
          id: string
          individual_health: string | null
          indoor_housework: string | null
          investment_plan: string | null
          job_expenses: string | null
          job_title: string | null
          last_name: string | null
          life_insurance: string | null
          marital_status: string | null
          matter_no: string | null
          meal_prep: string | null
          opposing_counsel_firm: string | null
          opposing_economist: string | null
          other_benefits: string | null
          other_dependents: Json | null
          overtime: string | null
          pet_care: string | null
          retirement_age: string | null
          retirement_plan: string | null
          salary: string | null
          settlement_date: string | null
          skills_licenses: string | null
          start_date: string | null
          state: string | null
          status: string
          stock_options: string | null
          submitted_by: string
          trial_date: string | null
          trial_location: string | null
          updated_at: string
          uploaded_files: Json | null
          vehicle_maintenance: string | null
          work_duties: string | null
          work_missed: string | null
          work_steady: string | null
          zip_code: string | null
        }
        Insert: {
          additional_info?: string | null
          address1?: string | null
          address2?: string | null
          advancements?: string | null
          bonus?: string | null
          career_trajectory?: string | null
          city?: string | null
          created_at?: string
          date_of_birth?: string | null
          date_of_death?: string | null
          defendant?: string | null
          dependent_care?: string | null
          education_level?: string | null
          employer_name?: string | null
          employment_status?: string | null
          employment_years?: Json | null
          errands?: string | null
          ethnicity?: string | null
          family_health?: string | null
          firm_id?: string | null
          first_name?: string | null
          gender?: string | null
          health_issues?: string | null
          home_maintenance?: string | null
          household_dependents?: Json | null
          id?: string
          individual_health?: string | null
          indoor_housework?: string | null
          investment_plan?: string | null
          job_expenses?: string | null
          job_title?: string | null
          last_name?: string | null
          life_insurance?: string | null
          marital_status?: string | null
          matter_no?: string | null
          meal_prep?: string | null
          opposing_counsel_firm?: string | null
          opposing_economist?: string | null
          other_benefits?: string | null
          other_dependents?: Json | null
          overtime?: string | null
          pet_care?: string | null
          retirement_age?: string | null
          retirement_plan?: string | null
          salary?: string | null
          settlement_date?: string | null
          skills_licenses?: string | null
          start_date?: string | null
          state?: string | null
          status?: string
          stock_options?: string | null
          submitted_by: string
          trial_date?: string | null
          trial_location?: string | null
          updated_at?: string
          uploaded_files?: Json | null
          vehicle_maintenance?: string | null
          work_duties?: string | null
          work_missed?: string | null
          work_steady?: string | null
          zip_code?: string | null
        }
        Update: {
          additional_info?: string | null
          address1?: string | null
          address2?: string | null
          advancements?: string | null
          bonus?: string | null
          career_trajectory?: string | null
          city?: string | null
          created_at?: string
          date_of_birth?: string | null
          date_of_death?: string | null
          defendant?: string | null
          dependent_care?: string | null
          education_level?: string | null
          employer_name?: string | null
          employment_status?: string | null
          employment_years?: Json | null
          errands?: string | null
          ethnicity?: string | null
          family_health?: string | null
          firm_id?: string | null
          first_name?: string | null
          gender?: string | null
          health_issues?: string | null
          home_maintenance?: string | null
          household_dependents?: Json | null
          id?: string
          individual_health?: string | null
          indoor_housework?: string | null
          investment_plan?: string | null
          job_expenses?: string | null
          job_title?: string | null
          last_name?: string | null
          life_insurance?: string | null
          marital_status?: string | null
          matter_no?: string | null
          meal_prep?: string | null
          opposing_counsel_firm?: string | null
          opposing_economist?: string | null
          other_benefits?: string | null
          other_dependents?: Json | null
          overtime?: string | null
          pet_care?: string | null
          retirement_age?: string | null
          retirement_plan?: string | null
          salary?: string | null
          settlement_date?: string | null
          skills_licenses?: string | null
          start_date?: string | null
          state?: string | null
          status?: string
          stock_options?: string | null
          submitted_by?: string
          trial_date?: string | null
          trial_location?: string | null
          updated_at?: string
          uploaded_files?: Json | null
          vehicle_maintenance?: string | null
          work_duties?: string | null
          work_missed?: string | null
          work_steady?: string | null
          zip_code?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "wrongful_death_drafts_normalized_firm_id_fkey"
            columns: ["firm_id"]
            isOneToOne: false
            referencedRelation: "firms"
            referencedColumns: ["id"]
          },
        ]
      }
      wrongful_death_forms: {
        Row: {
          additional_info: string
          address1: string
          address2: string | null
          advancements: string
          bonus: string | null
          career_trajectory: string
          city: string
          created_at: string
          date_of_birth: string
          date_of_death: string
          defendant: string | null
          dependent_care: string
          education_level: string
          employer_name: string
          employment_status: string
          employment_years: Json | null
          errands: string
          ethnicity: string
          family_health: string | null
          firm_id: string | null
          first_name: string
          gender: string
          health_issues: string
          home_maintenance: string
          household_dependents: Json | null
          id: string
          individual_health: string | null
          indoor_housework: string
          investment_plan: string | null
          job_expenses: string
          job_title: string
          last_name: string
          life_insurance: string | null
          marital_status: string
          matter_no: string | null
          meal_prep: string
          opposing_counsel_firm: string
          opposing_economist: string
          other_benefits: string | null
          other_dependents: Json | null
          overtime: string
          pet_care: string
          retirement_age: string
          retirement_plan: string | null
          salary: string
          settlement_date: string
          skills_licenses: string
          start_date: string
          state: string
          status: string
          stock_options: string | null
          submitted_by: string
          trial_date: string
          trial_location: string
          updated_at: string
          uploaded_files: Json | null
          vehicle_maintenance: string
          version: number | null
          version_history: Json | null
          work_duties: string
          work_missed: string
          work_steady: string
          zip_code: string
        }
        Insert: {
          additional_info: string
          address1: string
          address2?: string | null
          advancements: string
          bonus?: string | null
          career_trajectory: string
          city: string
          created_at?: string
          date_of_birth: string
          date_of_death: string
          defendant?: string | null
          dependent_care: string
          education_level: string
          employer_name: string
          employment_status: string
          employment_years?: Json | null
          errands: string
          ethnicity: string
          family_health?: string | null
          firm_id?: string | null
          first_name: string
          gender: string
          health_issues: string
          home_maintenance: string
          household_dependents?: Json | null
          id?: string
          individual_health?: string | null
          indoor_housework: string
          investment_plan?: string | null
          job_expenses: string
          job_title: string
          last_name: string
          life_insurance?: string | null
          marital_status: string
          matter_no?: string | null
          meal_prep: string
          opposing_counsel_firm: string
          opposing_economist: string
          other_benefits?: string | null
          other_dependents?: Json | null
          overtime: string
          pet_care: string
          retirement_age: string
          retirement_plan?: string | null
          salary: string
          settlement_date: string
          skills_licenses: string
          start_date: string
          state: string
          status?: string
          stock_options?: string | null
          submitted_by: string
          trial_date: string
          trial_location: string
          updated_at?: string
          uploaded_files?: Json | null
          vehicle_maintenance: string
          version?: number | null
          version_history?: Json | null
          work_duties: string
          work_missed: string
          work_steady: string
          zip_code: string
        }
        Update: {
          additional_info?: string
          address1?: string
          address2?: string | null
          advancements?: string
          bonus?: string | null
          career_trajectory?: string
          city?: string
          created_at?: string
          date_of_birth?: string
          date_of_death?: string
          defendant?: string | null
          dependent_care?: string
          education_level?: string
          employer_name?: string
          employment_status?: string
          employment_years?: Json | null
          errands?: string
          ethnicity?: string
          family_health?: string | null
          firm_id?: string | null
          first_name?: string
          gender?: string
          health_issues?: string
          home_maintenance?: string
          household_dependents?: Json | null
          id?: string
          individual_health?: string | null
          indoor_housework?: string
          investment_plan?: string | null
          job_expenses?: string
          job_title?: string
          last_name?: string
          life_insurance?: string | null
          marital_status?: string
          matter_no?: string | null
          meal_prep?: string
          opposing_counsel_firm?: string
          opposing_economist?: string
          other_benefits?: string | null
          other_dependents?: Json | null
          overtime?: string
          pet_care?: string
          retirement_age?: string
          retirement_plan?: string | null
          salary?: string
          settlement_date?: string
          skills_licenses?: string
          start_date?: string
          state?: string
          status?: string
          stock_options?: string | null
          submitted_by?: string
          trial_date?: string
          trial_location?: string
          updated_at?: string
          uploaded_files?: Json | null
          vehicle_maintenance?: string
          version?: number | null
          version_history?: Json | null
          work_duties?: string
          work_missed?: string
          work_steady?: string
          zip_code?: string
        }
        Relationships: [
          {
            foreignKeyName: "wrongful_death_forms_normalized_firm_id_fkey"
            columns: ["firm_id"]
            isOneToOne: false
            referencedRelation: "firms"
            referencedColumns: ["id"]
          },
        ]
      }
      wrongful_termination_drafts: {
        Row: {
          additional_info: string | null
          address1: string | null
          address2: string | null
          city: string | null
          created_at: string
          date_of_birth: string | null
          date_of_termination: string | null
          defendant: string | null
          email: string | null
          ethnicity: string | null
          firm_id: string | null
          first_name: string | null
          gender: string | null
          id: string
          last_name: string | null
          marital_status: string | null
          matter_no: string | null
          opposing_counsel_firm: string | null
          opposing_economist: string | null
          phone_number: string | null
          phone_type: string | null
          post_termination_advancements: string | null
          post_termination_bonus: string | null
          post_termination_duties: string | null
          post_termination_education: string | null
          post_termination_employer: string | null
          post_termination_employment_status: string | null
          post_termination_family_health: string | null
          post_termination_individual_health: string | null
          post_termination_investment_plan: string | null
          post_termination_job_expenses: string | null
          post_termination_job_title: string | null
          post_termination_life_insurance: string | null
          post_termination_other_benefits: string | null
          post_termination_overtime: string | null
          post_termination_retirement_age: string | null
          post_termination_retirement_plan: string | null
          post_termination_salary: string | null
          post_termination_start_date: string | null
          post_termination_stock_options: string | null
          post_termination_work_steady: string | null
          post_termination_years: Json | null
          pre_termination_advancements: string | null
          pre_termination_bonus: string | null
          pre_termination_career_trajectory: string | null
          pre_termination_duties: string | null
          pre_termination_education: string | null
          pre_termination_education_plans: string | null
          pre_termination_employer: string | null
          pre_termination_employment_status: string | null
          pre_termination_family_health: string | null
          pre_termination_individual_health: string | null
          pre_termination_investment_plan: string | null
          pre_termination_job_expenses: string | null
          pre_termination_job_title: string | null
          pre_termination_life_insurance: string | null
          pre_termination_other_benefits: string | null
          pre_termination_overtime: string | null
          pre_termination_retirement_age: string | null
          pre_termination_retirement_plan: string | null
          pre_termination_salary: string | null
          pre_termination_skills: string | null
          pre_termination_start_date: string | null
          pre_termination_stock_options: string | null
          pre_termination_work_steady: string | null
          pre_termination_years: Json | null
          settlement_date: string | null
          state: string | null
          status: string
          submitted_by: string
          trial_date: string | null
          trial_location: string | null
          updated_at: string
          uploaded_files: Json | null
          zip_code: string | null
        }
        Insert: {
          additional_info?: string | null
          address1?: string | null
          address2?: string | null
          city?: string | null
          created_at?: string
          date_of_birth?: string | null
          date_of_termination?: string | null
          defendant?: string | null
          email?: string | null
          ethnicity?: string | null
          firm_id?: string | null
          first_name?: string | null
          gender?: string | null
          id?: string
          last_name?: string | null
          marital_status?: string | null
          matter_no?: string | null
          opposing_counsel_firm?: string | null
          opposing_economist?: string | null
          phone_number?: string | null
          phone_type?: string | null
          post_termination_advancements?: string | null
          post_termination_bonus?: string | null
          post_termination_duties?: string | null
          post_termination_education?: string | null
          post_termination_employer?: string | null
          post_termination_employment_status?: string | null
          post_termination_family_health?: string | null
          post_termination_individual_health?: string | null
          post_termination_investment_plan?: string | null
          post_termination_job_expenses?: string | null
          post_termination_job_title?: string | null
          post_termination_life_insurance?: string | null
          post_termination_other_benefits?: string | null
          post_termination_overtime?: string | null
          post_termination_retirement_age?: string | null
          post_termination_retirement_plan?: string | null
          post_termination_salary?: string | null
          post_termination_start_date?: string | null
          post_termination_stock_options?: string | null
          post_termination_work_steady?: string | null
          post_termination_years?: Json | null
          pre_termination_advancements?: string | null
          pre_termination_bonus?: string | null
          pre_termination_career_trajectory?: string | null
          pre_termination_duties?: string | null
          pre_termination_education?: string | null
          pre_termination_education_plans?: string | null
          pre_termination_employer?: string | null
          pre_termination_employment_status?: string | null
          pre_termination_family_health?: string | null
          pre_termination_individual_health?: string | null
          pre_termination_investment_plan?: string | null
          pre_termination_job_expenses?: string | null
          pre_termination_job_title?: string | null
          pre_termination_life_insurance?: string | null
          pre_termination_other_benefits?: string | null
          pre_termination_overtime?: string | null
          pre_termination_retirement_age?: string | null
          pre_termination_retirement_plan?: string | null
          pre_termination_salary?: string | null
          pre_termination_skills?: string | null
          pre_termination_start_date?: string | null
          pre_termination_stock_options?: string | null
          pre_termination_work_steady?: string | null
          pre_termination_years?: Json | null
          settlement_date?: string | null
          state?: string | null
          status?: string
          submitted_by: string
          trial_date?: string | null
          trial_location?: string | null
          updated_at?: string
          uploaded_files?: Json | null
          zip_code?: string | null
        }
        Update: {
          additional_info?: string | null
          address1?: string | null
          address2?: string | null
          city?: string | null
          created_at?: string
          date_of_birth?: string | null
          date_of_termination?: string | null
          defendant?: string | null
          email?: string | null
          ethnicity?: string | null
          firm_id?: string | null
          first_name?: string | null
          gender?: string | null
          id?: string
          last_name?: string | null
          marital_status?: string | null
          matter_no?: string | null
          opposing_counsel_firm?: string | null
          opposing_economist?: string | null
          phone_number?: string | null
          phone_type?: string | null
          post_termination_advancements?: string | null
          post_termination_bonus?: string | null
          post_termination_duties?: string | null
          post_termination_education?: string | null
          post_termination_employer?: string | null
          post_termination_employment_status?: string | null
          post_termination_family_health?: string | null
          post_termination_individual_health?: string | null
          post_termination_investment_plan?: string | null
          post_termination_job_expenses?: string | null
          post_termination_job_title?: string | null
          post_termination_life_insurance?: string | null
          post_termination_other_benefits?: string | null
          post_termination_overtime?: string | null
          post_termination_retirement_age?: string | null
          post_termination_retirement_plan?: string | null
          post_termination_salary?: string | null
          post_termination_start_date?: string | null
          post_termination_stock_options?: string | null
          post_termination_work_steady?: string | null
          post_termination_years?: Json | null
          pre_termination_advancements?: string | null
          pre_termination_bonus?: string | null
          pre_termination_career_trajectory?: string | null
          pre_termination_duties?: string | null
          pre_termination_education?: string | null
          pre_termination_education_plans?: string | null
          pre_termination_employer?: string | null
          pre_termination_employment_status?: string | null
          pre_termination_family_health?: string | null
          pre_termination_individual_health?: string | null
          pre_termination_investment_plan?: string | null
          pre_termination_job_expenses?: string | null
          pre_termination_job_title?: string | null
          pre_termination_life_insurance?: string | null
          pre_termination_other_benefits?: string | null
          pre_termination_overtime?: string | null
          pre_termination_retirement_age?: string | null
          pre_termination_retirement_plan?: string | null
          pre_termination_salary?: string | null
          pre_termination_skills?: string | null
          pre_termination_start_date?: string | null
          pre_termination_stock_options?: string | null
          pre_termination_work_steady?: string | null
          pre_termination_years?: Json | null
          settlement_date?: string | null
          state?: string | null
          status?: string
          submitted_by?: string
          trial_date?: string | null
          trial_location?: string | null
          updated_at?: string
          uploaded_files?: Json | null
          zip_code?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "wrongful_termination_drafts_normalized_firm_id_fkey"
            columns: ["firm_id"]
            isOneToOne: false
            referencedRelation: "firms"
            referencedColumns: ["id"]
          },
        ]
      }
      wrongful_termination_forms: {
        Row: {
          additional_info: string
          address1: string
          address2: string | null
          city: string
          created_at: string
          date_of_birth: string
          date_of_termination: string
          defendant: string | null
          email: string
          ethnicity: string
          firm_id: string | null
          first_name: string
          gender: string
          id: string
          last_name: string
          marital_status: string
          matter_no: string | null
          opposing_counsel_firm: string
          opposing_economist: string
          phone_number: string
          phone_type: string
          post_termination_advancements: string | null
          post_termination_bonus: string | null
          post_termination_duties: string | null
          post_termination_education: string
          post_termination_employer: string | null
          post_termination_employment_status: string | null
          post_termination_family_health: string | null
          post_termination_individual_health: string | null
          post_termination_investment_plan: string | null
          post_termination_job_expenses: string | null
          post_termination_job_title: string | null
          post_termination_life_insurance: string | null
          post_termination_other_benefits: string | null
          post_termination_overtime: string | null
          post_termination_retirement_age: string | null
          post_termination_retirement_plan: string | null
          post_termination_salary: string | null
          post_termination_start_date: string | null
          post_termination_stock_options: string | null
          post_termination_work_steady: string | null
          post_termination_years: Json | null
          pre_termination_advancements: string
          pre_termination_bonus: string | null
          pre_termination_career_trajectory: string
          pre_termination_duties: string
          pre_termination_education: string
          pre_termination_education_plans: string
          pre_termination_employer: string
          pre_termination_employment_status: string
          pre_termination_family_health: string | null
          pre_termination_individual_health: string | null
          pre_termination_investment_plan: string | null
          pre_termination_job_expenses: string
          pre_termination_job_title: string
          pre_termination_life_insurance: string | null
          pre_termination_other_benefits: string | null
          pre_termination_overtime: string
          pre_termination_retirement_age: string
          pre_termination_retirement_plan: string | null
          pre_termination_salary: string
          pre_termination_skills: string
          pre_termination_start_date: string
          pre_termination_stock_options: string | null
          pre_termination_work_steady: string
          pre_termination_years: Json | null
          settlement_date: string
          state: string
          status: string
          submitted_by: string
          trial_date: string
          trial_location: string
          updated_at: string
          uploaded_files: Json | null
          version: number | null
          version_history: Json | null
          zip_code: string
        }
        Insert: {
          additional_info: string
          address1: string
          address2?: string | null
          city: string
          created_at?: string
          date_of_birth: string
          date_of_termination: string
          defendant?: string | null
          email: string
          ethnicity: string
          firm_id?: string | null
          first_name: string
          gender: string
          id?: string
          last_name: string
          marital_status: string
          matter_no?: string | null
          opposing_counsel_firm: string
          opposing_economist: string
          phone_number: string
          phone_type: string
          post_termination_advancements?: string | null
          post_termination_bonus?: string | null
          post_termination_duties?: string | null
          post_termination_education: string
          post_termination_employer?: string | null
          post_termination_employment_status?: string | null
          post_termination_family_health?: string | null
          post_termination_individual_health?: string | null
          post_termination_investment_plan?: string | null
          post_termination_job_expenses?: string | null
          post_termination_job_title?: string | null
          post_termination_life_insurance?: string | null
          post_termination_other_benefits?: string | null
          post_termination_overtime?: string | null
          post_termination_retirement_age?: string | null
          post_termination_retirement_plan?: string | null
          post_termination_salary?: string | null
          post_termination_start_date?: string | null
          post_termination_stock_options?: string | null
          post_termination_work_steady?: string | null
          post_termination_years?: Json | null
          pre_termination_advancements: string
          pre_termination_bonus?: string | null
          pre_termination_career_trajectory: string
          pre_termination_duties: string
          pre_termination_education: string
          pre_termination_education_plans: string
          pre_termination_employer: string
          pre_termination_employment_status: string
          pre_termination_family_health?: string | null
          pre_termination_individual_health?: string | null
          pre_termination_investment_plan?: string | null
          pre_termination_job_expenses: string
          pre_termination_job_title: string
          pre_termination_life_insurance?: string | null
          pre_termination_other_benefits?: string | null
          pre_termination_overtime: string
          pre_termination_retirement_age: string
          pre_termination_retirement_plan?: string | null
          pre_termination_salary: string
          pre_termination_skills: string
          pre_termination_start_date: string
          pre_termination_stock_options?: string | null
          pre_termination_work_steady: string
          pre_termination_years?: Json | null
          settlement_date: string
          state: string
          status?: string
          submitted_by: string
          trial_date: string
          trial_location: string
          updated_at?: string
          uploaded_files?: Json | null
          version?: number | null
          version_history?: Json | null
          zip_code: string
        }
        Update: {
          additional_info?: string
          address1?: string
          address2?: string | null
          city?: string
          created_at?: string
          date_of_birth?: string
          date_of_termination?: string
          defendant?: string | null
          email?: string
          ethnicity?: string
          firm_id?: string | null
          first_name?: string
          gender?: string
          id?: string
          last_name?: string
          marital_status?: string
          matter_no?: string | null
          opposing_counsel_firm?: string
          opposing_economist?: string
          phone_number?: string
          phone_type?: string
          post_termination_advancements?: string | null
          post_termination_bonus?: string | null
          post_termination_duties?: string | null
          post_termination_education?: string
          post_termination_employer?: string | null
          post_termination_employment_status?: string | null
          post_termination_family_health?: string | null
          post_termination_individual_health?: string | null
          post_termination_investment_plan?: string | null
          post_termination_job_expenses?: string | null
          post_termination_job_title?: string | null
          post_termination_life_insurance?: string | null
          post_termination_other_benefits?: string | null
          post_termination_overtime?: string | null
          post_termination_retirement_age?: string | null
          post_termination_retirement_plan?: string | null
          post_termination_salary?: string | null
          post_termination_start_date?: string | null
          post_termination_stock_options?: string | null
          post_termination_work_steady?: string | null
          post_termination_years?: Json | null
          pre_termination_advancements?: string
          pre_termination_bonus?: string | null
          pre_termination_career_trajectory?: string
          pre_termination_duties?: string
          pre_termination_education?: string
          pre_termination_education_plans?: string
          pre_termination_employer?: string
          pre_termination_employment_status?: string
          pre_termination_family_health?: string | null
          pre_termination_individual_health?: string | null
          pre_termination_investment_plan?: string | null
          pre_termination_job_expenses?: string
          pre_termination_job_title?: string
          pre_termination_life_insurance?: string | null
          pre_termination_other_benefits?: string | null
          pre_termination_overtime?: string
          pre_termination_retirement_age?: string
          pre_termination_retirement_plan?: string | null
          pre_termination_salary?: string
          pre_termination_skills?: string
          pre_termination_start_date?: string
          pre_termination_stock_options?: string | null
          pre_termination_work_steady?: string
          pre_termination_years?: Json | null
          settlement_date?: string
          state?: string
          status?: string
          submitted_by?: string
          trial_date?: string
          trial_location?: string
          updated_at?: string
          uploaded_files?: Json | null
          version?: number | null
          version_history?: Json | null
          zip_code?: string
        }
        Relationships: [
          {
            foreignKeyName: "wrongful_termination_forms_normalized_firm_id_fkey"
            columns: ["firm_id"]
            isOneToOne: false
            referencedRelation: "firms"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      analyze_document_relationships: {
        Args: {
          max_relationships?: number
          similarity_threshold?: number
          source_document_id: string
        }
        Returns: {
          confidence_score: number
          related_doc_type: string
          related_document_id: string
          related_title: string
          relationship_type: string
          shared_chunks: number
        }[]
      }
      binary_quantize: {
        Args: { "": string } | { "": unknown }
        Returns: unknown
      }
      check_document_duplicate: {
        Args: { content_hash?: string; filename?: string }
        Returns: Json
      }
      check_document_exists_by_hash: {
        Args: { content_hash_input: string }
        Returns: {
          created_at: string
          document_exists: boolean
          document_id: string
          filename: string
          title: string
        }[]
      }
      create_batch_file: {
        Args: {
          p_batch_id: string
          p_file_id: string
          p_file_size: number
          p_mime_type: string
          p_original_filename: string
          p_status?: string
          p_stored_path: string
        }
        Returns: undefined
      }
      create_batch_job: {
        Args: { p_batch_id: string; p_status?: string; p_total_files: number }
        Returns: undefined
      }
      create_document: {
        Args: {
          p_content_hash: string
          p_doc_type: string
          p_document_id: string
          p_file_size: number
          p_filename: string
          p_mime_type: string
          p_title: string
          p_word_count: number
        }
        Returns: string
      }
      create_document_chunk: {
        Args: {
          p_chunk_id: string
          p_chunk_index: number
          p_content: string
          p_content_hash: string
          p_document_id: string
          p_embedding: string
          p_token_count: number
        }
        Returns: undefined
      }
      create_form_audit_entry: {
        Args: {
          p_action_type: string
          p_firm_id: string
          p_form_id: string
          p_form_type: string
          p_metadata: Json
          p_submitted_by: string
        }
        Returns: undefined
      }
      fetch_all: {
        Args: { p_params?: Json; p_query: string }
        Returns: Json
      }
      fetch_documents_paginated: {
        Args: {
          doc_type_filter?: string
          jurisdiction_filter?: string
          page_limit?: number
          page_offset?: number
          practice_area_filter?: string
          search_term?: string
          sort_by?: string
          sort_order?: string
        }
        Returns: Json
      }
      fetch_one: {
        Args: { p_params?: Json; p_query: string }
        Returns: Json
      }
      generate_slug: {
        Args: { input_text: string }
        Returns: string
      }
      get_batch_files: {
        Args: { p_batch_id: string }
        Returns: Json
      }
      get_batch_job_status: {
        Args: { p_batch_id: string }
        Returns: Json
      }
      get_database_summary: {
        Args: Record<PropertyKey, never>
        Returns: Json
      }
      get_document_type_counts: {
        Args: Record<PropertyKey, never>
        Returns: {
          count: number
          doc_type: string
        }[]
      }
      get_document_url: {
        Args: { path: string }
        Returns: string
      }
      get_firm_users_with_details: {
        Args: { firm_id_param: string }
        Returns: {
          email: string
          first_name: string
          id: string
          last_name: string
          role: string
          saved_forms_count: number
          submitted_forms_count: number
          user_id: string
        }[]
      }
      get_search_analytics: {
        Args: { days_back?: number }
        Returns: Json
      }
      halfvec_avg: {
        Args: { "": number[] }
        Returns: unknown
      }
      halfvec_out: {
        Args: { "": unknown }
        Returns: unknown
      }
      halfvec_send: {
        Args: { "": unknown }
        Returns: string
      }
      halfvec_typmod_in: {
        Args: { "": unknown[] }
        Returns: number
      }
      hnsw_bit_support: {
        Args: { "": unknown }
        Returns: unknown
      }
      hnsw_halfvec_support: {
        Args: { "": unknown }
        Returns: unknown
      }
      hnsw_sparsevec_support: {
        Args: { "": unknown }
        Returns: unknown
      }
      hnswhandler: {
        Args: { "": unknown }
        Returns: unknown
      }
      ingest_batch_file_with_metadata: {
        Args: { p_batch_id: string; p_file_id: string; p_metadata: Json }
        Returns: Json
      }
      is_rag_admin: {
        Args: { user_email: string }
        Returns: boolean
      }
      ivfflat_bit_support: {
        Args: { "": unknown }
        Returns: unknown
      }
      ivfflat_halfvec_support: {
        Args: { "": unknown }
        Returns: unknown
      }
      ivfflathandler: {
        Args: { "": unknown }
        Returns: unknown
      }
      l2_norm: {
        Args: { "": unknown } | { "": unknown }
        Returns: number
      }
      l2_normalize: {
        Args: { "": string } | { "": unknown } | { "": unknown }
        Returns: string
      }
      match_documents: {
        Args: {
          match_count?: number
          match_threshold?: number
          query_embedding: string
        }
        Returns: {
          chunk_id: string
          chunk_index: number
          content: string
          document_id: string
          filename: string
          similarity: number
          title: string
        }[]
      }
      process_batch_documents: {
        Args: { documents_data: Json; job_id: string }
        Returns: Json
      }
      search_documents: {
        Args:
          | {
              filter_doc_type?: string
              match_count?: number
              match_threshold?: number
              query_embedding: string
            }
          | {
              filter_doc_type?: string
              match_count?: number
              match_threshold?: number
              query_embedding: string
            }
          | {
              match_count?: number
              match_threshold?: number
              query_embedding: string
            }
        Returns: {
          chunk_id: string
          chunk_index: number
          content: string
          doc_type: string
          document_id: string
          filename: string
          similarity: number
          title: string
        }[]
      }
      semantic_search_with_filters: {
        Args: {
          date_from?: string
          date_to?: string
          doc_type_filter?: string
          jurisdiction_filter?: string
          practice_area_filter?: string
          query_embedding: string
          result_limit?: number
          similarity_threshold?: number
        }
        Returns: {
          chunk_id: string
          chunk_index: number
          chunk_text: string
          date_added: string
          doc_type: string
          document_id: string
          filename: string
          jurisdiction: string
          practice_area: string
          similarity: number
          title: string
        }[]
      }
      sparsevec_out: {
        Args: { "": unknown }
        Returns: unknown
      }
      sparsevec_send: {
        Args: { "": unknown }
        Returns: string
      }
      sparsevec_typmod_in: {
        Args: { "": unknown[] }
        Returns: number
      }
      update_batch_file_status: {
        Args: {
          p_document_id?: string
          p_error_message?: string
          p_file_id: string
          p_status: string
        }
        Returns: undefined
      }
      update_batch_job_status: {
        Args: {
          p_batch_id: string
          p_completed_files?: number
          p_error_message?: string
          p_failed_files?: number
          p_new_status?: string
          p_processed_files?: number
        }
        Returns: undefined
      }
      vector_avg: {
        Args: { "": number[] }
        Returns: string
      }
      vector_dims: {
        Args: { "": string } | { "": unknown }
        Returns: number
      }
      vector_norm: {
        Args: { "": string }
        Returns: number
      }
      vector_out: {
        Args: { "": string }
        Returns: unknown
      }
      vector_send: {
        Args: { "": string }
        Returns: string
      }
      vector_typmod_in: {
        Args: { "": unknown[] }
        Returns: number
      }
    }
    Enums: {
      doc_category_enum: "PI" | "WD" | "EM" | "BV" | "Other"
      doc_type_enum:
        | "book"
        | "article"
        | "statute"
        | "case_law"
        | "expert_report"
        | "other"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {
      doc_category_enum: ["PI", "WD", "EM", "BV", "Other"],
      doc_type_enum: [
        "book",
        "article",
        "statute",
        "case_law",
        "expert_report",
        "other",
      ],
    },
  },
} as const
