'use client';
import { motion, AnimatePresence } from 'framer-motion';

export interface ShoppingItem {
  item: string;
  category: string;
  quantity: number;
  size?: string;
  brand?: string;
}

interface ShoppingListProps {
  items: ShoppingItem[];
}

export function ShoppingList({ items }: ShoppingListProps) {
  if (items.length === 0) {
    return (
      <div className="text-center text-gray-500 py-10">
        <p>Your shopping list is empty.</p>
        <p className="text-sm mt-2">Try saying "Add 2 apples"</p>
      </div>
    );
  }

  // Group by category
  const grouped = items.reduce((acc, item) => {
    const cat = item.category || 'Other';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(item);
    return acc;
  }, {} as Record<string, ShoppingItem[]>);

  return (
    <div className="w-full max-w-md mx-auto space-y-6">
      {Object.entries(grouped).map(([category, catItems]) => (
        <div key={category} className="bg-gray-900 rounded-lg p-4 border border-gray-800">
          <h3 className="text-amber-500 font-semibold mb-3 border-b border-gray-800 pb-2 uppercase text-xs tracking-wider">
            {category}
          </h3>
          <ul className="space-y-2">
            <AnimatePresence>
              {catItems.map((item, idx) => (
                <motion.li
                  key={`${item.item}-${idx}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className="flex items-center justify-between text-gray-200"
                >
                  <div className="flex flex-col">
                    <span className="font-medium capitalize">{item.item}</span>
                    {item.brand && <span className="text-xs text-gray-500">{item.brand}</span>}
                  </div>
                  <div className="text-gray-400 bg-gray-800 px-2 py-1 rounded text-sm">
                    {item.quantity} {item.size || ''}
                  </div>
                </motion.li>
              ))}
            </AnimatePresence>
          </ul>
        </div>
      ))}
    </div>
  );
}
