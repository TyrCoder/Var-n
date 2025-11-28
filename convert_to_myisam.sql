-- Fix InnoDB issue by converting all tables to MyISAM
ALTER TABLE `activity_logs` ENGINE=MyISAM;
ALTER TABLE `addresses` ENGINE=MyISAM;
ALTER TABLE `admin_settings` ENGINE=MyISAM;
ALTER TABLE `cart` ENGINE=MyISAM;
ALTER TABLE `categories` ENGINE=MyISAM;
ALTER TABLE `inventory` ENGINE=MyISAM;
ALTER TABLE `journal_entries` ENGINE=MyISAM;
ALTER TABLE `order_items` ENGINE=MyISAM;
ALTER TABLE `orders` ENGINE=MyISAM;
ALTER TABLE `otp_verifications` ENGINE=MyISAM;
ALTER TABLE `product_archive_requests` ENGINE=MyISAM;
ALTER TABLE `product_edits` ENGINE=MyISAM;
ALTER TABLE `product_images` ENGINE=MyISAM;
ALTER TABLE `product_variants` ENGINE=MyISAM;
ALTER TABLE `products` ENGINE=MyISAM;
ALTER TABLE `promotions` ENGINE=MyISAM;
ALTER TABLE `reviews` ENGINE=MyISAM;
ALTER TABLE `rider_transactions` ENGINE=MyISAM;
ALTER TABLE `riders` ENGINE=MyISAM;
ALTER TABLE `sellers` ENGINE=MyISAM;
ALTER TABLE `shipments` ENGINE=MyISAM;
ALTER TABLE `transactions` ENGINE=MyISAM;
ALTER TABLE `users` ENGINE=MyISAM;

SELECT 'All tables converted to MyISAM' as status;
