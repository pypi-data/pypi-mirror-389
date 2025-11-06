


def plot_columns(df, columns, plot_type='count', n_cols=3, main_title=None, target=None, theme='Set2'):
    
    import matplotlib.pyplot as plt
    import seaborn as sns
    import math
    """
    Smart plotting function for EDA — creates multiple plots in grid layout.

    Parameters:
    -----------
    df : pandas.DataFrame
        Dataset to plot.
    columns : list
        List of column names to visualize.
    plot_type : str
        Type of plot. Choose from: 'count', 'hist', 'box', 'violin'
    n_cols : int
        Number of plots per row (default = 3)
    main_title : str
        Optional main title for the figure.
    target : str or None
        Optional target variable for hue (e.g., 'y')
    theme : str
        Choose plot color theme: 'Set2', 'coolwarm', or 'skyblue'
    """

    # Validate theme
    valid_themes = ['Set2', 'coolwarm', 'skyblue']
    if theme not in valid_themes:
        print(f"⚠️ Invalid theme! Using default 'Set2'.")
        theme = 'Set2'

    # Handle theme settings
    if theme == 'skyblue':
        palette = None
        color = 'skyblue'
    else:
        palette = theme
        color = None

    # Safety: Limit max plots
    max_plots = 12
    if len(columns) > max_plots:
        print(f"⚠️ Too many columns! Showing first {max_plots} only.")
        columns = columns[:max_plots]

    n_plots = len(columns)
    n_rows = math.ceil(n_plots / n_cols)

    plt.figure(figsize=(5 * n_cols, 4 * n_rows))

    for i, col in enumerate(columns, 1):
        plt.subplot(n_rows, n_cols, i)

        # Select hue only if target is provided
        hue_param = target if target else None

        # ---- Choose plot type ----
        if plot_type == 'count':
            sns.countplot(data=df, x=col, hue=hue_param, palette=palette, color=color)
        elif plot_type == 'hist':
            sns.histplot(data=df, x=col, hue=hue_param, kde=True, palette=palette, color=color)
        elif plot_type == 'box':
            if hue_param:
                sns.boxplot(data=df, x=hue_param, y=col, palette=palette, color=color)
            else:
                sns.boxplot(data=df, y=col, palette=palette, color=color)
        elif plot_type == 'violin':
            if hue_param:
                sns.violinplot(data=df, x=hue_param, y=col, palette=palette, color=color)
            else:
                sns.violinplot(data=df, y=col, palette=palette, color=color)
        else:
            raise ValueError("Invalid plot_type. Use: 'count', 'hist', 'box', or 'violin'")

        plt.title(f"{col}", fontsize=12)
        plt.xticks(rotation=45)
        plt.tight_layout()

    if main_title:
        plt.suptitle(main_title, fontsize=16, y=1.02)

    plt.show()



def plot_confusion_matrices(y_test, predictions_dict):
    import matplotlib.pyplot as plt
    import seaborn as sns
    from sklearn.metrics import confusion_matrix as cfm
    """
    Displays confusion matrices for multiple models in 3 columns layout.
    
    Parameters:
        y_test : array-like
            True labels of the test data.
        predictions_dict : dict
            Dictionary with model names as keys and predicted values as values.
            Example: {'Logistic Regression': y_pred_log, 'SVM': y_pred_svm, ...}
    
            predictions = {
        'Logistic Regression': y_pred_log,
        'Random Forest': y_pred_rf,
        'KNN': y_pred_knn,
        'SVM': y_pred_svm,
        'XGBoost': y_pred_xg
        }
    
    """
    
    n_models = len(predictions_dict)
    n_cols = 3
    n_rows = (n_models + n_cols - 1) // n_cols   # auto adjust rows
    
    plt.figure(figsize=(18, 5 * n_rows))
    
    for i, (model_name, y_pred) in enumerate(predictions_dict.items(), 1):
        plt.subplot(n_rows, n_cols, i)
        cm = cfm(y_test, y_pred)
        sns.heatmap(cm, annot=True, cmap='Blues', fmt='d', cbar=False)
        plt.title(f"{model_name} - Confusion Matrix")
        plt.xlabel("Predicted")
        plt.ylabel("Actual")
    
    plt.tight_layout()
    plt.show()

