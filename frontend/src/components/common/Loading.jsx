const Loading = ({ size = 'md', text = 'Đang tải...' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div
        className={`${sizeClasses[size]} border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin`}
      />
      {text && <p className="mt-4 text-gray-500">{text}</p>}
    </div>
  );
};

export default Loading;
